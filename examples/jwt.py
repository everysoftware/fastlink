from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Response, Depends

from auth365.backend import JWTBackend
from auth365.exceptions import Auth365Error
from auth365.fastapi.transport import CookieTransport
from auth365.schemas import JWTConfig, OAuth2PasswordRequest, JWTPayload

app = FastAPI()

transport = CookieTransport()
backend = JWTBackend(JWTConfig(type="access", key="secret"))


@app.post("/login")
def login(form: Annotated[OAuth2PasswordRequest, Form()]) -> Response:
    if form.username != "admin" or form.password != "admin":
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = backend.create("access", JWTPayload(sub=form.username))
    return transport.set_token(Response(), token)


@app.get("/me")
def get_me(token: Annotated[str, Depends(transport)]) -> JWTPayload:
    try:
        payload = backend.validate("access", token)
    except Auth365Error as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    return payload
