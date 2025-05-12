# FastLink

**Effortless asynchronous OAuth 2.0 client for popular platforms**

---

[![Test](https://github.com/everysoftware/fastid/actions/workflows/test.yml/badge.svg)](https://github.com/everysoftware/fastid/actions/workflows/test.yml)
[![CodeQL Advanced](https://github.com/everysoftware/fastid/actions/workflows/codeql.yml/badge.svg)](https://github.com/everysoftware/fastid/actions/workflows/codeql.yml)

---

## Features

- **Asynchronous**: Built on top of `httpx` is fully asynchronous.
- **Built-in support**: For popular OAuth 2.0 providers like **Google**, **Yandex**, **Telegram**, etc.
- **Extensible**: Easily add support for new OAuth 2.0 providers.
- **Easy to use**: Simple and intuitive API.

## Installation

```bash
pip install fastlink
```

## Get Started

```python
from typing import Annotated

from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse

from fastlink.google.client import GoogleOAuth
from fastlink.schemas import OAuth2Callback, OpenID
from examples.config import settings

app = FastAPI()

oauth = GoogleOAuth(
    settings.google_client_id,
    settings.google_client_secret,
    "http://localhost:8000/callback",
)


@app.get("/login")
async def login() -> RedirectResponse:
    async with oauth:
        url = await oauth.get_authorization_url()
        return RedirectResponse(url=url)


@app.get("/callback")
async def oauth_callback(callback: Annotated[OAuth2Callback, Depends()]) -> OpenID:
    async with oauth:
        await oauth.authorize(callback)
        return await oauth.userinfo()

```

Now you can run the server and visit `http://localhost:8000/login` to start the OAuth 2.0 flow.

![screenshot-1738081195921.png](assets/screenshot-1738081195921.png)

After logging into Google, you will be redirected to the callback URL. The server will then fetch the user's OpenID
information and return it as a response.
![screenshot-1738081352079.png](assets/screenshot-1738081352079.png)
