from collections.abc import AsyncIterator, Sequence
from typing import Any, Self
from urllib.parse import urlencode

from aiogram import Bot
from aiogram.utils.token import TokenValidationError

from fastlink.base.utils import replace_localhost
from fastlink.exceptions import TokenError
from fastlink.schemas import DiscoveryDocument, OpenID, ProviderMeta
from fastlink.telegram.schemas import TelegramCallback, TelegramWidget
from fastlink.telegram.utils import check_expiration, verify_hmac_sha256


class TelegramSSO:
    meta = ProviderMeta(
        name="telegram",
        title="Telegram",
        discovery=DiscoveryDocument(authorization_endpoint="https://oauth.telegram.org/auth"),
        scope=["write"],
    )
    widget_js_url = "https://telegram.org/js/telegram-widget.js?22"

    def __init__(
        self,
        bot_token: str,
        widget_uri: str | None = None,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
        expires_in: int = 300,
        **bot_kwargs: Any,
    ) -> None:
        assert self.meta.scope is not None

        self.bot_token = bot_token
        self.redirect_uri = redirect_uri
        self.widget_uri = widget_uri
        self.scope = scope or self.meta.scope
        self.expires_in = expires_in

        try:
            self.bot = Bot(bot_token, **bot_kwargs)
        except TokenValidationError as e:
            raise TokenError from e

        self.bot_id = self.bot.id
        self._callback: TelegramCallback | None = None

    @property
    def discovery(self) -> DiscoveryDocument:
        assert self.meta.discovery is not None
        return self.meta.discovery

    async def widget_info(self) -> TelegramWidget:
        me = await self.bot.me()
        return TelegramWidget(
            bot_username=me.username,
            callback_url=replace_localhost(self.redirect_uri or self.redirect_uri),
            scope=" ".join(self.scope),
        )

    async def widget(self) -> str:
        info = await self.widget_info()
        return f"""
            <html>
                <head>
                    <title>Telegram OAuth</title>
                </head>
                <body>
                    <script async src="{self.widget_js_url}" data-telegram-login="{info.bot_username}"
                    data-size="medium" data-auth-url="{info.callback_url}" data-request-access="{info.scope}"></script>
                </body>
            </html>
            """

    async def login_url(
        self,
        *,
        widget_uri: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        params = params or {}
        widget_uri = replace_localhost(widget_uri or self.widget_uri)
        scope = self.scope
        login_params = {
            "bot_id": self.bot_id,
            "origin": widget_uri,
            "request_access": scope,
            **params,
        }
        return f"{self.discovery.authorization_endpoint}?{urlencode(login_params)}"

    async def login(self, call: TelegramCallback) -> None:
        self._callback = call
        response = call.model_dump(exclude_none=True)
        expected_hash = response.pop("hash")
        verify_hmac_sha256(response, expected_hash, self.bot_token)
        check_expiration(response, self.expires_in)

    async def userinfo(self) -> dict[str, Any]:
        assert self._callback is not None
        return self._callback.model_dump(exclude_none=True)

    async def callback_raw(self, call: TelegramCallback) -> dict[str, Any]:
        await self.login(call)
        return await self.userinfo()

    async def openid_from_response(self, response: dict[str, Any]) -> OpenID:
        first_name, last_name = (
            response["first_name"],
            response.get("last_name"),
        )
        display_name = f"{first_name} {last_name}" if last_name else first_name
        return OpenID(
            id=str(response["id"]),
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            picture=response.get("photo_url"),
        )

    async def openid(self) -> OpenID:
        return await self.openid_from_response(await self.userinfo())

    async def callback(self, call: TelegramCallback) -> OpenID:
        await self.login(call)
        return await self.openid()

    async def __aenter__(self) -> Self:
        await self.bot.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.bot.__aexit__(exc_type, exc_value, traceback)

    async def __call__(self) -> AsyncIterator[Self]:
        async with self:
            yield self
