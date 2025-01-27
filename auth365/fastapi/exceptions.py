from auth365.exceptions import Auth365Error


class NoTokenProvided(Auth365Error):
    pass


class InvalidToken(Auth365Error):
    pass


class InvalidTokenType(Auth365Error):
    pass
