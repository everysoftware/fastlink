import datetime
from typing import TYPE_CHECKING

import jwt
from jwt import InvalidTokenError as JWTInvalidTokenError

from fastlink.exceptions import InvalidTokenError, InvalidTokenTypeError
from fastlink.jwt.schemas import JWTConfig, JWTPayload

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class JWTManager:
    def __init__(self, *config: JWTConfig) -> None:
        self.config: MutableMapping[str, JWTConfig] = {t.type: t for t in config}

    def create(self, token_type: str, payload: JWTPayload) -> str:
        config = self.config[token_type]
        now = datetime.datetime.now(datetime.UTC)
        claims = dict(
            iss=config.issuer,
            typ=token_type,
            iat=now,
            **payload.model_dump(exclude_none=True),
        )
        if config.expires_in is not None:
            claims["exp"] = now + config.expires_in
        return jwt.encode(
            claims,
            config.private_key,
            algorithm=config.algorithm,
        )

    def validate(
        self,
        token_type: str,
        token: str,
    ) -> JWTPayload:
        params = self.config[token_type]
        try:
            decoded = jwt.decode(
                token,
                params.public_key,
                algorithms=[params.algorithm],
                issuer=params.issuer,
            )
        except JWTInvalidTokenError as e:
            raise InvalidTokenError from e
        if decoded["typ"] != token_type:
            raise InvalidTokenTypeError
        return JWTPayload.model_validate(decoded)

    def get_lifetime(self, token_type: str) -> int | None:
        expires_in = self.config[token_type].expires_in
        if expires_in is None:
            return None
        return int(expires_in.total_seconds())
