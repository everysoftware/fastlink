from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from fastlink import FastLink
from fastlink.schemas import OAuth2Callback, OpenID, ProviderMeta


class SSOBase(FastLink, ABC):
    meta: ProviderMeta

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
        scope: Sequence[str] | None = None,
    ) -> None:
        super().__init__(self.meta, client_id, client_secret, redirect_uri, scope)

    @abstractmethod
    async def openid_from_response(
        self,
        response: dict[str, Any],
    ) -> OpenID: ...

    async def openid(self) -> OpenID:
        return await self.openid_from_response(await self.userinfo())

    async def callback(self, call: OAuth2Callback) -> OpenID:
        await self.login(call)
        return await self.openid()
