from pydantic import BaseModel


class LoginData(BaseModel):
    message: str
    signed_message: str
