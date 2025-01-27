from abc import ABC, abstractmethod
from typing import (
    Any,
    Sequence,
    Self,
    AsyncIterator,
)
from urllib.parse import urlencode

import httpx

from auth365.providers.exceptions import (
    DiscoveryUnavailable,
    TokenUnavailable,
    ClientUnavailable,
    NoRedirectURI,
    AuthorizationFailed,
    UserinfoFailed,
    NoState,
)
from auth365.schemas import DiscoveryDocument, TokenResponse, OAuth2Callback, OpenID
from auth365.utils import generate_random_state


class OAuth2Client(ABC):
    provider: str = NotImplemented
    default_scope: Sequence[str] = []

    @property
    @abstractmethod
    def discovery(self) -> DiscoveryDocument: ...

    @property
    @abstractmethod
    def token(self) -> TokenResponse: ...

    @abstractmethod
    async def get_authorization_url(
        self,
        *,
        scope: Sequence[str] | None = None,
        redirect_uri: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str: ...

    @abstractmethod
    async def authorize(
        self,
        callback: OAuth2Callback,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TokenResponse: ...

    @abstractmethod
    async def userinfo(self) -> OpenID: ...

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...


class HttpxClient(OAuth2Client, ABC):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
        *,
        use_state: bool = True,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope or self.default_scope
        self.use_state = use_state

        self._token: TokenResponse | None = None
        self._discovery: DiscoveryDocument | None = None
        self._client: httpx.AsyncClient | None = None

    @abstractmethod
    async def discover(self) -> DiscoveryDocument: ...

    @abstractmethod
    async def openid_from_response(
        self,
        response: dict[Any, Any],
    ) -> OpenID: ...

    @property
    def discovery(self) -> DiscoveryDocument:
        if self._discovery is None:
            raise DiscoveryUnavailable("Discovery document is not available. Please discover first.")
        return self._discovery

    @property
    def token(self) -> TokenResponse:
        if not self._token:
            raise TokenUnavailable("Token is not available. Please authorize first.")
        return self._token

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise ClientUnavailable("Client is not available. Please enter the context.")
        return self._client

    async def get_authorization_url(
        self,
        *,
        scope: Sequence[str] | None = None,
        redirect_uri: str | None = None,
        state: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        params = params or {}
        if self.use_state:
            params |= {"state": state or generate_random_state()}
        redirect_uri = redirect_uri or self.redirect_uri
        if redirect_uri is None:
            raise NoRedirectURI("redirect_uri must be provided, either at construction or request time")
        request_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "scope": " ".join(scope or self.scope),
            "redirect_uri": redirect_uri,
            **params,
        }
        return f"{self.discovery.authorization_endpoint}?{urlencode(request_params)}"

    async def authorize(
        self,
        callback: OAuth2Callback,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TokenResponse:
        request = self._prepare_token_request(callback, body=body, headers=headers)
        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        response = await self.client.send(
            request,
            auth=auth,
        )
        content = response.json()
        if response.status_code < 200 or response.status_code > 299:
            raise AuthorizationFailed("Authorization failed: %s", content)
        self._token = TokenResponse.model_validate(content)
        return self._token

    async def userinfo(self) -> OpenID:
        assert self.discovery.userinfo_endpoint is not None
        headers = {
            "Authorization": f"{self.token.token_type} {self.token.access_token}",
        }
        response = await self.client.get(self.discovery.userinfo_endpoint, headers=headers)
        content = response.json()
        if response.status_code < 200 or response.status_code > 299:
            raise UserinfoFailed("Getting userinfo failed: %s", content)
        return await self.openid_from_response(content)

    def _prepare_token_request(
        self,
        callback: OAuth2Callback,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Request:
        assert self.discovery.token_endpoint is not None
        body = body or {}
        headers = headers or {}
        headers |= {"Content-Type": "application/x-www-form-urlencoded"}
        if self.use_state:
            if not callback.state:
                raise NoState("State was not found in the callback")
            body |= {"state": callback.state}
        body = {
            "grant_type": "authorization_code",
            "code": callback.code,
            "redirect_uri": callback.redirect_uri or self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            **body,
        }
        return httpx.Request(
            "post",
            self.discovery.token_endpoint,
            data=body,
            headers=headers,
        )

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient()
        await self._client.__aenter__()
        if self._discovery is None:
            self._discovery = await self.discover()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._token = None
        await self.client.__aexit__(exc_type, exc_value, traceback)

    async def __call__(self) -> AsyncIterator[Self]:
        async with self as oauth:
            yield oauth
