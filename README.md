# FastLink

_OAuth 2.0 client for various platforms, asynchronous, easy-to-use, extensible_

---

[![Test](https://github.com/everysoftware/fastlink/actions/workflows/test.yml/badge.svg)](https://github.com/everysoftware/fastlink/actions/workflows/test.yml)
[![CodeQL Advanced](https://github.com/everysoftware/fastlink/actions/workflows/codeql.yml/badge.svg)](https://github.com/everysoftware/fastlink/actions/workflows/codeql.yml)

---

## Features

- **All-in-one**: Supports popular platforms like **Google**, **Yandex**, **Telegram**, etc.
- **Asynchronous**: Built on top of `httpx` is fully asynchronous.
- **Easy-to-use**: Simple and intuitive API for quick integration.
- **Extensible**: Easily add support for new platforms or customize existing ones.

## Installation

```bash
pip install fastlink
```

## Get Started

```python
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

```

Now you can run the server and visit `http://localhost:8000/login` to start the OAuth 2.0 flow.

![screenshot-1738081195921.png](assets/screenshot-1738081195921.png)

After logging into Google, you will be redirected to the callback URL. The server will then fetch the user's OpenID
information and return it as a response.
![screenshot-1738081352079.png](assets/screenshot-1738081352079.png)
