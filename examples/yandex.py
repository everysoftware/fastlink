from typing import Annotated

from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse

from examples.config import settings
from fastlink import YandexSSO
from fastlink.schemas import OAuth2Callback, OpenID

app = FastAPI()

oauth = YandexSSO(
    settings.yandex_client_id,
    settings.yandex_client_secret,
    "http://localhost:8000/callback",
)


@app.get("/login")
async def login() -> RedirectResponse:
    async with oauth:
        url = await oauth.login_url()
        return RedirectResponse(url=url)


@app.get("/callback")
async def callback(call: Annotated[OAuth2Callback, Depends()]) -> OpenID:
    async with oauth:
        return await oauth.callback(call)
