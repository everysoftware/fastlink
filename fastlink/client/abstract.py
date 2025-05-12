from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Self

from fastlink.schemas import DiscoveryDocument, OAuth2Callback, OpenID, TokenResponse


class Client(ABC):
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
