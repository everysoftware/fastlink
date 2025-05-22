from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from examples.config import settings
from fastlink import TelegramSSO
from fastlink.schemas import OpenID
from fastlink.telegram.schemas import TelegramCallback

app = FastAPI()

oauth = TelegramSSO(settings.telegram_bot_token, "http://localhost:8000/widget", "http://localhost:8000/callback")


@app.get("/login")
async def login() -> RedirectResponse:
    async with oauth:
        url = await oauth.login_url()
        return RedirectResponse(url=url)


@app.get("/widget")
async def widget() -> HTMLResponse:
    async with oauth:
        content = await oauth.widget()
        return HTMLResponse(content=content)


@app.get("/callback")
async def callback(call: Annotated[TelegramCallback, Depends()]) -> OpenID:
    async with oauth:
        return await oauth.callback(call)
