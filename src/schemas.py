from pydantic import BaseModel


class UserCreate(BaseModel):
    id: int


class GenerateCodeRequest(BaseModel):
    user_id: int


class VerificationCodeRequest(BaseModel):
    user_id: int
    input_code: int
