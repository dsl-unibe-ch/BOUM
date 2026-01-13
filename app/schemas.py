from pydantic import BaseModel

class UserSimpleDTO(BaseModel):
    username: str
    password: str

