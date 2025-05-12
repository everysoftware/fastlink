from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Response

from fastlink.client.schemas import OAuth2PasswordRequest
from fastlink.exceptions import FastLinkError
from fastlink.integrations.fastapi.transport import CookieTransport
from fastlink.jwt.manager import JWTManager
from fastlink.jwt.schemas import JWTConfig, JWTPayload

app = FastAPI()

transport = CookieTransport()
manager = JWTManager(JWTConfig(type="access", key="secret"))


@app.post("/login")
def login(form: Annotated[OAuth2PasswordRequest, Form()]) -> Response:
    if form.username != "admin" or form.password != "admin":  # noqa: S105
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = manager.create("access", JWTPayload(sub=form.username))
    return transport.set_token(Response(), token)


@app.get("/me")
def get_me(token: Annotated[str, Depends(transport)]) -> JWTPayload:
    try:
        payload = manager.validate("access", token)
    except FastLinkError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    return payload
