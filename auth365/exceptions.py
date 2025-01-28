class Auth365Error(Exception):
    pass


class TokenUnavailable(Auth365Error):
    pass


class DiscoveryUnavailable(Auth365Error):
    pass


class ClientUnavailable(Auth365Error):
    pass


class NoRedirectURI(Auth365Error):
    pass


class AuthorizationFailed(Auth365Error):
    pass


class UserinfoFailed(Auth365Error):
    pass


class NoState(Auth365Error):
    pass


class NoTokenProvided(Auth365Error):
    pass


class InvalidToken(Auth365Error):
    pass


class InvalidTokenType(Auth365Error):
    pass
