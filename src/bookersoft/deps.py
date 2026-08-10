from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: int
    username: str


def get_current_user() -> CurrentUser:
    return CurrentUser(id=1, username="owner")
