from pydantic import BaseModel, HttpUrl, PositiveInt, PositiveFloat

from .account import Account


class Config(BaseModel):
    accounts: list[Account]
    referral_code: str | int

    mint_rpc_url: HttpUrl
    arb_rpc_url: HttpUrl

    threads: PositiveInt

    min_delay_before_start: PositiveInt
    max_delay_before_start: PositiveInt

    comet_bridge_wallet: str
    comet_bridge_amount_min: PositiveFloat
    comet_bridge_amount_max: PositiveFloat

    mint_random_all_nfts: list[str]
    delay_between_mint_min: PositiveInt
    delay_between_mint_max: PositiveInt

    find_and_steal_percentage_range_start: int
    find_and_steal_percentage_range_end: int
    find_and_steal_min_amount: int

    spin_turntable_by_percentage_of_energy: int
    module: str = ""
