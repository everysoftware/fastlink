from typing import Any

from fastlink.base.provider import SSOBase
from fastlink.exceptions import FastLinkError
from fastlink.schemas import OpenID, ProviderMeta


class GoogleSSO(SSOBase):
    meta = ProviderMeta(
        name="google", title="Google", server_url="https://accounts.google.com", scope=["openid", "email", "profile"]
    )

    async def openid_from_response(
        self,
        response: dict[Any, Any],
    ) -> OpenID:
        if response.get("email_verified"):
            return OpenID(
                email=response.get("email"),
                id=response.get("sub"),
                first_name=response.get("given_name"),
                last_name=response.get("family_name"),
                display_name=response.get("name"),
                picture=response.get("picture"),
            )
        raise FastLinkError(f"User {response.get('email')} is not verified with Google")
