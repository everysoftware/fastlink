import datetime
from enum import StrEnum, auto
from typing import Sequence, Literal
from urllib.parse import urlencode

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_serializer, EmailStr


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(use_enum_values=True)


class OAuth2Grant(StrEnum):
    """
    Grants are methods through which a client can obtain an access token.
    """

    client_credentials = auto()
    """
    The client requests an access token from the authorization server's token endpoint by including its client
    credentials (client_id and client_secret). This is used when the client is acting on its own behalf.
    """
    password = auto()
    """
    The resource owner provides the client with its username and password.
    The client requests an access token from the authorization server's token endpoint by including the credentials
    received from the resource owner.

    This grant type should only be used when there is a high degree of trust between the resource owner and the client.
    """
    implicit = auto()
    """
    The client directs the resource owner to the authorization server. The resource owner authenticates and
    authorizes the client. The authorization server redirects the resource owner back to the client with an access
    token.

    This grant type is used for clients that are implemented in a browser using a scripting language such as JavaScript.
    """
    authorization_code = auto()
    """
    The client directs the resource owner to an authorization server. The resource owner authenticates and authorizes
    the client. The authorization server redirects the resource owner back to the client with an authorization code.
    The client requests an access token from the authorization server's token endpoint by including the authorization
    code received in the previous step.
    """
    pkce = auto()
    """
    The client directs the resource owner to an authorization server. The resource owner authenticates and authorizes
    the client. The authorization server redirects the resource owner back to the client with an authorization code.
    The client requests an access token from the authorization server's token endpoint by including the authorization
    code received in the previous step and the code verifier.
    """
    refresh_token = auto()
    """
    The client requests an access token from the authorization server's token endpoint by including the refresh token
    """


class OAuth2ConsentRequest(BaseModel):
    """
    Consent Request is sent by the client to the authorization server.
    Authorization server asks the resource owner to grant permissions to the client.
    """

    response_type: str | None = None
    """
    The response type is used to specify the desired authorization processing flow.
    """
    client_id: str | None = None
    """
    The client ID is a public identifier for the client.
    """
    redirect_uri: str | None = None
    """
    The redirect URI is used to redirect the user-agent back to the client.
    """
    scope: str | None = None
    """
    The scope is used to specify what access rights an access token has.
    """
    state: str | None = None
    """
    The state is used to prevent CSRF attacks.
    """
    code_challenge: str | None = None
    """
    The code challenge is used to verify the authorization code.
    """
    code_challenge_method: str | None = None
    """
    The code challenge method is used to verify the authorization code.
    """

    @property
    def scopes(self) -> Sequence[str]:
        if self.scope is None:
            return []
        return self.scope.split(" ")


class OAuth2Callback(BaseModel):
    """
    Callback is sent by the authorization server to the client after the resource owner grants permissions.
    """

    code: str | None = None
    """
    The authorization code is used to obtain an access token.
    """
    state: str | None = None
    """
    The state is used to prevent CSRF attacks. State should be the same as in the consent request.
    """
    scope: str | None = None
    """
    The scope is used to specify what access rights an access token has. Scope should be the same as in the consent
    request.
    """
    code_verifier: str | None = None
    """
    The code verifier is used to verify the authorization code.
    """
    redirect_uri: str | None = None
    """
    The redirect URI is used to redirect the user-agent back to the client. Not all providers put it in the callback.
    """

    def get_url(self) -> str:
        return f"{self.redirect_uri}?{urlencode(self.model_dump(mode='json', exclude_none=True))}"


class OAuth2BaseTokenRequest(BaseModel):
    grant_type: OAuth2Grant
    """
    The grant type is used to specify the method through which a client can obtain an access token.
    """
    client_id: str = ""
    """
    The client ID is a public identifier for the client.

    Client credentials may be omitted if the resource server trusts the client. E.g. if you are connecting
    backend and frontend of the same application.
    """
    client_secret: str = ""
    """
    The client secret is a secret known only to the client and the resource server.

    May be omitted if the request comes from public clients (e.g. web browser).
    Client credentials may be omitted if the resource server trusts the client. E.g. if you are connecting
    backend and frontend of the same application.
    """

    model_config = ConfigDict(from_attributes=True)


class OAuth2PasswordRequest(OAuth2BaseTokenRequest):
    grant_type: OAuth2Grant = OAuth2Grant.password
    username: str = ""
    """
    The resource owner's username. Used in Password Grant Flow.
    """
    password: str = ""
    """
    The resource owner's password. Used in Password Grant Flow.
    """
    scope: str = ""
    """
    The scope is used to specify what access rights an access token has.

    Usually, it is passed as query params in the authorization URL, but if the flow does not assume redirection
    (like Password Grant Flow), it should be passed in the token request.
    """


class OAuth2AuthorizationCodeRequest(OAuth2BaseTokenRequest):
    grant_type: OAuth2Grant = OAuth2Grant.authorization_code
    code: str
    """
    The authorization code is used to obtain an access token. Used in Authorization Code Grant.
    """
    code_verifier: str = ""
    """
    The code verifier is used to verify the authorization code. Used in PKCE Grant.
    """
    redirect_uri: str = ""
    """
    The redirect URI is passed as second factor to authorize the client.

    Usually we passed the redirect URI in authorization URL, but some providers like Google oblige to pass it in token
    request too.
    """


class OAuth2RefreshTokenRequest(OAuth2BaseTokenRequest):
    grant_type: OAuth2Grant = OAuth2Grant.refresh_token
    refresh_token: str
    """
    The refresh token is used to obtain a new access token. Used in Refresh Token Grant.
    """


class OAuth2TokenRequest(BaseModel):
    """
    Token Request is sent by the client to the authorization server to obtain an access token.
    """

    grant_type: OAuth2Grant
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    password: str = ""
    code: str = ""
    code_verifier: str = ""
    redirect_uri: str = ""
    refresh_token: str = ""
    scope: str = ""

    @property
    def scopes(self) -> Sequence[str]:
        return self.scope.split(" ")

    def as_password_grant(self) -> OAuth2PasswordRequest:
        return OAuth2PasswordRequest.model_validate(self)

    def as_authorization_code_grant(
        self,
    ) -> OAuth2AuthorizationCodeRequest:
        return OAuth2AuthorizationCodeRequest.model_validate(self)

    def as_refresh_token_grant(self) -> OAuth2RefreshTokenRequest:
        return OAuth2RefreshTokenRequest.model_validate(self)


class TokenResponse(BaseModel):
    """
    Token Response is sent by the authorization server to the client and contains the access token.
    """

    token_id: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str | None = "Bearer"
    scope: str | None = None
    expires_in: int | None = Field(
        None,
        description="Token expiration time in seconds",
    )

    model_config = ConfigDict(extra="allow")


class DiscoveryDocument(BaseModel):
    """
    Discovery Document is a JSON document that contains key-value pairs of metadata about the OpenID Connect provider.
    """

    issuer: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    jwks_uri: str | None = None
    scopes_supported: Sequence[str] | None = None
    response_types_supported: Sequence[str] | None = None
    grant_types_supported: Sequence[str] | None = None
    subject_types_supported: Sequence[str] | None = None
    id_token_signing_alg_values_supported: Sequence[str] | None = None
    claims_supported: Sequence[str] | None = None

    model_config = ConfigDict(extra="allow")


class JWK(BaseModel):
    """
    JSON Web Key (JWK) is a JSON object that represents a cryptographic key.
    """

    kty: str
    use: str
    alg: str
    kid: str
    n: str
    e: str

    model_config = ConfigDict(extra="allow")


class JWKS(BaseModel):
    keys: Sequence[JWK]


class JWT(BaseModel):
    """
    JSON Web Token (JWT) Claims are the JSON objects that contain the information about the user and the token itself.
    """

    iss: str | None = None
    sub: str | None = None
    aud: str | None = None
    typ: str | None = None
    iat: datetime.datetime | None = None
    exp: datetime.datetime | None = None

    @field_serializer("iat", "exp", mode="plain")
    def datetime_to_timestamp(self, value: datetime.datetime | None) -> int | None:
        if value is None:
            return value
        return int(value.timestamp())

    model_config = ConfigDict(extra="allow")


class AccessToken(JWT):
    """
    Access Token is a JSON Web Token (JWT) that contains the information about the user and the permissions that the
    user has. Access Token is used to access the protected resources.
    """

    scope: str | None = None

    @property
    def scopes(self) -> Sequence[str]:
        if self.scope is None:
            return []
        return self.scope.split(" ")


class RefreshToken(JWT):
    """
    Refresh Token is a JSON Web Token (JWT) that used to obtain a new Access Token when the current Access Token
    expires. Refresh Token is used to refresh the Access Token without the need to re-authenticate the user.
    """

    scope: str | None = None


class IDToken(JWT):
    """
    ID Token is a JSON Web Token (JWT) that contains the information about the user and the authentication process.
    ID Token is used to authenticate the user and to obtain the user's information.
    """

    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email: EmailStr | None = None
    email_verified: bool | None = None


class JWTConfig(BaseModel):
    issuer: str
    algorithm: Literal["HS256", "RS256"] = "RS256"
    private_key: str
    public_key: str
    expires_in: datetime.timedelta | None = None


class OpenID(BaseModel):
    id: str
    provider: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    picture: str | None = None


class OpenIDBearer(OpenID, TokenResponse):
    pass


class TelegramCallback(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str
