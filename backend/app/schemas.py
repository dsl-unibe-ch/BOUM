from pydantic import BaseModel


class UserSimpleDTO(BaseModel):
    username: str
    password: str


class UserFullDTO(BaseModel):
    username: str
    password: str
    role: int | None = None
