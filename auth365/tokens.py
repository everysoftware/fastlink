import datetime
from typing import Any, Mapping, cast, MutableMapping

import jwt
from jwt import InvalidTokenError

from auth365.fastapi.exceptions import InvalidToken, InvalidTokenType
from auth365.schemas import TokenResponse, AccessToken, RefreshToken, IDToken, JWTConfig


class TokenManager:
    def __init__(self, types: MutableMapping[str, JWTConfig] | None = None) -> None:
        self.types: MutableMapping[str, JWTConfig] = types if types is not None else {}

    def create_at(self, claims: AccessToken) -> str:
        return self.create_custom(
            "access",
            claims.model_dump(),
        )

    def create_rt(self, claims: RefreshToken) -> str:
        return self.create_custom("refresh", claims.model_dump())

    def create_it(self, claims: IDToken) -> str:
        return self.create_custom(
            "id",
            claims.model_dump(),
        )

    def to_response(
        self,
        at: str | None = None,
        rt: str | None = None,
        it: str | None = None,
    ) -> TokenResponse:
        if rt is None:
            expires_in = self.get_lifetime("access")
        else:
            expires_in = self.get_lifetime("refresh")
        return TokenResponse(
            access_token=at,
            refresh_token=rt,
            id_token=it,
            expires_in=expires_in,
        )

    def validate_at(self, token: str) -> AccessToken:
        claims = self.validate_custom("access", token)
        return AccessToken.model_validate(claims)

    def validate_rt(self, token: str) -> RefreshToken:
        claims = self.validate_custom("refresh", token)
        return RefreshToken.model_validate(claims)

    def validate_it(self, token: str) -> IDToken:
        claims = self.validate_custom("id", token)
        return IDToken.model_validate(claims)

    def create_custom(self, token_type: str, payload: Mapping[str, Any]) -> str:
        params = self.get_type(token_type)
        now = datetime.datetime.now(datetime.UTC)
        claims = dict(
            iss=params.issuer,
            typ=token_type,
            iat=now,
            **payload,
        )
        if params.expires_in is not None:
            claims["exp"] = now + params.expires_in
        return jwt.encode(
            claims,
            params.private_key,
            algorithm=params.algorithm,
        )

    def validate_custom(
        self,
        token_type: str,
        token: str,
    ) -> Mapping[str, Any]:
        params = self.get_type(token_type)
        try:
            decoded = jwt.decode(
                token,
                params.public_key,
                algorithms=[params.algorithm],
                issuer=params.issuer,
            )
        except InvalidTokenError as e:
            raise InvalidToken() from e
        if decoded["typ"] != token_type:
            raise InvalidTokenType()
        return cast(Mapping[str, Any], decoded)

    def add_type(self, token_type: str, params: JWTConfig) -> None:
        self.types[token_type] = params

    def get_type(self, token_type: str) -> JWTConfig:
        return self.types[token_type]

    def has_type(self, token_type: str) -> bool:
        return token_type in self.types

    def get_lifetime(self, token_type: str) -> int | None:
        expires_in = self.types[token_type].expires_in
        if expires_in is None:
            return None
        return int(expires_in.total_seconds())
