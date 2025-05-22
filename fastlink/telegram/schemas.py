from fastlink.schemas import BaseModel


class TelegramCallback(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class TelegramWidget(BaseModel):
    bot_username: str
    callback_url: str
    scope: str = "write"
