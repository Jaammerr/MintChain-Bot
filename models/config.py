from pydantic import BaseModel, HttpUrl, PositiveInt, PositiveFloat

from .account import Account


class Config(BaseModel):
    accounts: list[Account]
    referral_code: str | int

    mint_rpc_url: HttpUrl | str
    op_rpc_url: HttpUrl | str
    threads: PositiveInt

    min_delay_before_start: PositiveInt
    max_delay_before_start: PositiveInt

    comet_bridge_amount_min: PositiveFloat
    comet_bridge_amount_max: PositiveFloat
    comet_bridge_wallet: str

    start_stealing_from_tree: PositiveInt

    spin_turntable_by_percentage_of_energy: int
    module: str = ""
