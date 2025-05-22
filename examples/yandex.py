from typing import Annotated

from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse

from examples.config import settings
from fastlink import YandexSSO
from fastlink.schemas import OAuth2Callback, OpenID

app = FastAPI()

sso = YandexSSO(
    settings.yandex_client_id,
    settings.yandex_client_secret,
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
