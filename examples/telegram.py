from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from examples.config import settings
from fastlink import TelegramAuth
from fastlink.schemas import OpenID
from fastlink.telegram.schemas import TelegramCallback

app = FastAPI()

oauth = TelegramAuth(
    settings.telegram_bot_token,
    "http://localhost:8000/widget",
)
CALLBACK_URL = "http://localhost:8000/callback"


@app.get("/login")
async def login() -> RedirectResponse:
    async with oauth:
        url = await oauth.get_authorization_url()
        return RedirectResponse(url=url)


@app.get("/widget")
def oauth_redirect() -> Any:
    text = f"""
    <html>
        <head>
            <title>Telegram OAuth</title>
        </head>
        <body>
            <script async src="https://telegram.org/js/telegram-widget.js?22" data-telegram-login="{settings.telegram_bot_username}"
            data-size="medium" data-auth-url="{CALLBACK_URL}" data-request-access="write"></script>
        </body>
    </html>
    """
    return HTMLResponse(content=text)


@app.get("/callback")
async def oauth_callback(callback: Annotated[TelegramCallback, Depends()]) -> OpenID:
    async with oauth:
        await oauth.authorize(callback)
        return await oauth.userinfo()
