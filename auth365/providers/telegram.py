import datetime
import hashlib
import hmac
from typing import Any, Sequence
from urllib.parse import urlencode

from auth365.exceptions import Auth365Error
from auth365.schemas import TokenResponse, OpenID, TelegramCallback, DiscoveryDocument
from auth365.utils import replace_localhost


class TelegramOAuth:
    provider: str = "telegram"
    default_scope: Sequence[str] = ["write"]

    def __init__(
        self,
        bot_token: str,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
        *,
        expires_in: int = 5 * 60,
    ) -> None:
        self.bot_token = bot_token
        self.redirect_uri = redirect_uri
        self.scope = scope if scope else self.default_scope
        self.expires_in = expires_in

        token_info = self.bot_token.split(":")
        if len(token_info) != 2:
            raise Auth365Error("Invalid bot token. It should be in the format: bot_id:bot_secret")
        self.bot_id = token_info[0]

        self._token: TokenResponse | None = None
        self._telegram_token: TelegramCallback | None = None

    @property
    def discovery(self) -> DiscoveryDocument:
        return DiscoveryDocument(authorization_endpoint="https://oauth.telegram.org/auth")

    @property
    def token(self) -> TokenResponse:
        if self._token is None:
            raise Auth365Error("No token available")
        return self._token

    @property
    def telegram_token(self) -> TelegramCallback:
        if self._telegram_token is None:
            raise Auth365Error("No Telegram token available. Please authorize first.")
        return self._telegram_token

    def openid_from_response(
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

    def get_authorization_url(
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
        code_hash = response.pop("hash")
        data_check_string = "\n".join(sorted(f"{k}={v}" for k, v in response.items()))
        computed_hash = hmac.new(
            hashlib.sha256(self.bot_token.encode()).digest(),
            data_check_string.encode(),
            "sha256",
        ).hexdigest()
        if not hmac.compare_digest(computed_hash, code_hash):
            raise Auth365Error("Invalid Telegram auth data: hash mismatch")
        dt = datetime.datetime.fromtimestamp(response["auth_date"], tz=datetime.UTC)
        now = datetime.datetime.now(tz=datetime.UTC)
        if now - dt > datetime.timedelta(seconds=self.expires_in):
            raise Auth365Error("Telegram auth data expired")
        self._token = TokenResponse(access_token=callback.hash)
        return self.token

    async def userinfo(self) -> OpenID:
        return self.openid_from_response(self.telegram_token.model_dump())
