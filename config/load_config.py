import os
import yaml

from loguru import logger
from models import Account, Config


def get_accounts() -> Account:
    accounts_path = os.path.join(os.path.dirname(__file__), "accounts.txt")
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
            if len(values) == 2:
                yield Account(auth_token=values[0].strip(), mnemonic=values[1].strip())

            elif len(values) == 3:
                yield Account(
                    auth_token=values[0].strip(),
                    mnemonic=values[1].strip(),
                    proxy=values[2].strip(),
                )

            else:
                logger.error(
                    f"Account <<{account}>> is not in correct format | Need to be in format: <<auth_token|mnemonic|proxy>>"
                )
                exit(1)


def load_config() -> Config:
    settings_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
    if not os.path.exists(settings_path):
        logger.error(f"File <<{settings_path}>> does not exist")
        exit(1)

    with open(settings_path, "r") as f:
        settings = yaml.safe_load(f)

    if not settings.get("referral_code"):
        logger.error(f"Referral code is not provided in settings.yaml")
        exit(1)

    if not settings.get("rpc_url"):
        logger.error(f"RPC URL is not provided in settings.yaml")
        exit(1)

    if not settings.get("iteration_delay"):
        logger.error(f"Iteration delay is not provided in settings.yaml")
        exit(1)

    return Config(
        accounts=list(get_accounts()),
        referral_code=settings["referral_code"],
        rpc_url=settings["rpc_url"],
        iteration_delay=settings["iteration_delay"],
    )
