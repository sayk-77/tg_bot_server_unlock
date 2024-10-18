from pydantic import BaseModel


class GenerateCodeRequest(BaseModel):
    account: str


class UserRequest(BaseModel):
    account: str
    code: int
