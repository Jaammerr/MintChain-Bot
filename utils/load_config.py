import os
import yaml
import random

from loguru import logger
from models import Account, Config


def get_accounts() -> Account:
    accounts_path = os.path.join(os.getcwd(), "config", "accounts.txt")
    if not os.path.exists(accounts_path):
        logger.error(f"File <<{accounts_path}>> does not exist")
        exit(1)

    with open(accounts_path, "r") as f:
        accounts = f.readlines()

        if not accounts:
            logger.error(f"File <<{accounts_path}>> is empty")
            exit(1)

        for account in accounts:
            values = account.split("|")
            if len(values) == 3:
                yield Account(
                    auth_token=values[0].strip(),
                    pk_or_mnemonic=values[1].strip(),
                    proxy=values[2].strip(),
                )

            else:
                logger.error(
                    f"Account <<{account}>> is not in correct format | Need to be in format: <<auth_token|mnemonic/pv_key|proxy>>"
                )
                exit(1)


def load_config() -> Config:
    settings_path = os.path.join(os.getcwd(), "config", "settings.yaml")
    if not os.path.exists(settings_path):
        logger.error(f"File <<{settings_path}>> does not exist")
        exit(1)

    with open(settings_path, "r") as f:
        settings = yaml.safe_load(f)

    REQUIRED_KEYS = (
        "referral_code",
        "mint_rpc_url",
        "arb_rpc_url",
        "threads",
        "min_delay_before_start",
        "max_delay_before_start",
        "spin_turntable_by_percentage_of_energy",
        "shuffle_accounts",
        "comet_bridge_amount_min",
        "comet_bridge_amount_max",
        "comet_bridge_wallet",
        "mint_random_all_nfts",
        "delay_between_mint_min",
        "delay_between_mint_max",
        "find_and_steal_percentage_range_start",
        "find_and_steal_percentage_range_end",
        "find_and_steal_min_amount"
    )

    for key in REQUIRED_KEYS:
        if key not in settings:
            logger.error(f"Key <<{key}>> is missing in settings.yaml")
            exit(1)

    accounts = list(get_accounts())
    if settings["shuffle_accounts"]:
        random.shuffle(accounts)

    return Config(accounts=accounts, **settings)
