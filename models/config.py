from pydantic import BaseModel, HttpUrl, PositiveInt

from .account import Account


class Config(BaseModel):
    accounts: list[Account]
    referral_code: str
    rpc_url: HttpUrl
    iteration_delay: PositiveInt
    threads: PositiveInt
