from collections.abc import Sequence
from typing import Any, Self
from urllib.parse import urlencode

from fastlink.client.schemas import DiscoveryDocument, OpenID, TokenResponse
from fastlink.client.utils import replace_localhost
from fastlink.constants import TELEGRAM_BOT_TOKEN_VALUES_NUMBER
from fastlink.exceptions import FastLinkError, InvalidBotTokenError
from fastlink.telegram.schemas import TelegramCallback
from fastlink.telegram.utils import check_expiration, verify_hmac_sha256


class TelegramAuth:
    provider: str = "telegram"
    default_scope: Sequence[str] = ["write"]

    def __init__(
        self,
        bot_token: str,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
        *,
        expires_in: int = 300,
    ) -> None:
        self.bot_token = bot_token
        self.redirect_uri = redirect_uri
        self.scope = scope if scope else self.default_scope
        self.expires_in = expires_in

        token_info = self.bot_token.split(":")
        if len(token_info) != TELEGRAM_BOT_TOKEN_VALUES_NUMBER:
            raise InvalidBotTokenError("Invalid bot token. It should be in the format: bot_id:bot_secret")
        self.bot_id = token_info[0]

        self._token: TokenResponse | None = None
        self._telegram_token: TelegramCallback | None = None

    @property
    def discovery(self) -> DiscoveryDocument:
        return DiscoveryDocument(authorization_endpoint="https://oauth.telegram.org/auth")

    @property
    def token(self) -> TokenResponse:
        if self._token is None:
            raise FastLinkError("No token available")
        return self._token

    @property
    def telegram_token(self) -> TelegramCallback:
        if self._telegram_token is None:
            raise FastLinkError("No Telegram token available. Please authorize first.")
        return self._telegram_token

    async def openid_from_response(
        self,
        response: dict[Any, Any],
    ) -> OpenID:
        first_name, last_name = (
            response["first_name"],
            response.get("last_name"),
        )
        display_name = f"{first_name} {last_name}" if first_name else first_name
        return OpenID(
            id=str(response["id"]),
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            picture=response.get("photo_url"),
            provider=self.provider,
        )

    async def get_authorization_url(
        self,
        *,
        scope: Sequence[str] | None = None,
        redirect_uri: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        params = params or {}
        redirect_uri = replace_localhost(redirect_uri or self.redirect_uri)
        login_params = {
            "bot_id": self.bot_id,
            "origin": redirect_uri,
            "request_access": scope or self.scope,
            **params,
        }
        return f"{self.discovery.authorization_endpoint}?{urlencode(login_params)}"

    async def authorize(self, callback: TelegramCallback) -> TokenResponse:
        self._telegram_token = callback
        response = callback.model_dump()
        expected_hash = response.pop("hash")
        verify_hmac_sha256(response, expected_hash, self.bot_token)
        check_expiration(response, self.expires_in)
        self._token = TokenResponse(access_token=callback.hash)
        return self.token

    async def userinfo(self) -> OpenID:
        return await self.openid_from_response(self.telegram_token.model_dump())

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass
