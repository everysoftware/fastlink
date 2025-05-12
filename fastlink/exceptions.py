class FastLinkError(Exception):
    pass


class TokenUnavailableError(FastLinkError):
    pass


class DiscoveryUnavailableError(FastLinkError):
    pass


class ClientUnavailableError(FastLinkError):
    pass


class NoRedirectURIError(FastLinkError):
    pass


class AuthorizationError(FastLinkError):
    pass


class UserinfoError(FastLinkError):
    pass


class StateError(FastLinkError):
    pass


class NoTokenProvidedError(FastLinkError):
    pass


class InvalidTokenError(FastLinkError):
    pass


class InvalidTokenTypeError(FastLinkError):
    pass


class InvalidBotTokenError(FastLinkError):
    pass


class HashMismatchError(FastLinkError):
    pass


class ExpirationError(FastLinkError):
    pass
