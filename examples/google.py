from typing import Annotated

from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse

from auth365.providers.google import GoogleOAuth
from auth365.schemas import OAuth2Callback, OpenID
from examples.config import settings

app = FastAPI()

google_oauth = GoogleOAuth(
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    redirect_uri="http://localhost:8000/callback",
)


@app.get("/login")
async def login() -> RedirectResponse:
    async with google_oauth:
        url = await google_oauth.get_authorization_url()
        return RedirectResponse(url=url)


@app.get("/callback")
async def oauth_callback(callback: Annotated[OAuth2Callback, Depends()]) -> OpenID:
    async with google_oauth:
        await google_oauth.authorize(callback)
        return await google_oauth.userinfo()
