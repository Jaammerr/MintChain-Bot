from pydantic import BaseModel, HttpUrl, PositiveInt, PositiveFloat

from .account import Account


class Config(BaseModel):
    accounts: list[Account]
    referral_code: str | int

    eth_rpc_url: HttpUrl
    sepolia_rpc_url: HttpUrl

    threads: PositiveInt

    min_delay_before_start: PositiveInt
    max_delay_before_start: PositiveInt

    min_amount_to_bridge: PositiveFloat
    max_amount_to_bridge: PositiveFloat

    spin_turntable_by_percentage_of_energy: int
    module: str = ""
