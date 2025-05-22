class FastLinkError(Exception):
    pass


class TokenError(FastLinkError):
    pass


class DiscoveryError(FastLinkError):
    pass


class ClientError(FastLinkError):
    pass


class RedirectURIError(FastLinkError):
    pass


class AuthorizationError(FastLinkError):
    pass


class UserinfoError(FastLinkError):
    pass


class StateError(FastLinkError):
    pass


class InvalidTokenTypeError(FastLinkError):
    pass


class HashMismatchError(FastLinkError):
    pass


class ExpirationError(FastLinkError):
    pass
