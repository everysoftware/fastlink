from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from examples.config import settings
from fastlink import GoogleSSO
from fastlink.schemas import OAuth2Callback, OpenID

app = FastAPI()

sso = GoogleSSO(
    settings.google_client_id,
    settings.google_client_secret,
    "http://localhost:8000/callback",
)


@app.get("/login")
async def login() -> RedirectResponse:
    async with sso:
        url = await sso.login_url()
        return RedirectResponse(url=url)


@app.get("/callback")
async def callback(call: Annotated[OAuth2Callback, Depends()]) -> OpenID:
    async with sso:
        return await sso.callback(call)
