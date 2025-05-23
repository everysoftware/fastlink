from collections.abc import AsyncIterator, Sequence
from typing import (
    Any,
    Self,
    cast,
)
from urllib.parse import urlencode

import httpx

from fastlink.base.utils import generate_random_state
from fastlink.constants import MAX_SUCCESS_CODE, MIN_SUCCESS_CODE
from fastlink.exceptions import (
    AuthorizationError,
    ClientError,
    DiscoveryError,
    RedirectURIError,
    StateError,
    TokenError,
    UserinfoError,
)
from fastlink.schemas import DiscoveryDocument, OAuth2Callback, ProviderMeta, TokenResponse


class FastLink:
    def __init__(
        self,
        meta: ProviderMeta,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.use_state = meta.use_state
        self.discovery_url = meta.discovery_url
        self._discovery = None

        scope = scope or meta.scope
        assert scope is not None
        self.scope = scope

        if meta.discovery is not None:
            self._discovery = meta.discovery

        if meta.server_url is not None:
            self.discovery_url = f"{meta.server_url}/.well-known/openid-configuration"

        self._token: TokenResponse | None = None
        self._client: httpx.AsyncClient | None = None

    @property
    def discovery(self) -> DiscoveryDocument:
        if self._discovery is None:
            raise DiscoveryError("Discovery document is not available. Please discover first.")
        return self._discovery

    @property
    def token(self) -> TokenResponse:
        if not self._token:
            raise TokenError("Token is not available. Please authorize first.")
        return self._token

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise ClientError("Client is not available. Please enter the context.")
        return self._client

    async def discover(self) -> DiscoveryDocument:
        assert self.discovery_url is not None
        response = await self.client.get(self.discovery_url)
        return DiscoveryDocument.model_validate(response.json())

    async def login_url(
        self,
        *,
        redirect_uri: str | None = None,
        state: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        params = params or {}
        if self.use_state:
            params |= {"state": state or generate_random_state()}
        redirect_uri = redirect_uri or self.redirect_uri
        if redirect_uri is None:
            raise RedirectURIError("redirect_uri must be provided, either at construction or request time")
        request_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "scope": " ".join(self.scope),
            "redirect_uri": redirect_uri,
            **params,
        }
        return f"{self.discovery.authorization_endpoint}?{urlencode(request_params)}"

    async def login(
        self,
        call: OAuth2Callback,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TokenResponse:
        request = self._prepare_token_request(call, body=body, headers=headers)
        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        response = await self.client.send(
            request,
            auth=auth,
        )
        content = response.json()
        if response.status_code < MIN_SUCCESS_CODE or response.status_code > MAX_SUCCESS_CODE:
            raise AuthorizationError("Authorization failed: %s", content)
        self._token = TokenResponse.model_validate(content)
        return self._token

    async def userinfo(self) -> dict[str, Any]:
        assert self.discovery.userinfo_endpoint is not None
        headers = {
            "Authorization": f"{self.token.token_type} {self.token.access_token}",
        }
        response = await self.client.get(self.discovery.userinfo_endpoint, headers=headers)
        content = response.json()
        if response.status_code < MIN_SUCCESS_CODE or response.status_code > MAX_SUCCESS_CODE:
            raise UserinfoError("Getting userinfo failed: %s", content)
        return cast("dict[str, Any]", content)

    async def callback_raw(self, call: OAuth2Callback) -> dict[str, Any]:
        await self.login(call)
        return await self.userinfo()

    def _prepare_token_request(
        self,
        call: OAuth2Callback,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Request:
        assert self.discovery.token_endpoint is not None
        body = body or {}
        headers = headers or {}
        headers |= {"Content-Type": "application/x-www-form-urlencoded"}
        if self.use_state:
            if not call.state:
                raise StateError("State was not found in the callback")
            body |= {"state": call.state}
        body = {
            "grant_type": "authorization_code",
            "code": call.code,
            "redirect_uri": call.redirect_uri or self.redirect_uri,
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
        async with self:
            yield self
