import asyncio
import sys
from typing import Any

import urllib3


from loguru import logger
from loader import config, semaphore
from core.bot import Bot
from models import Account
from console import Console
from utils import export_trees_ids


def setup():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level> {level: <8}</level> | - <white>{"
        "message}</white>",
    )
    logger.add("logs.log", rotation="1 day", retention="7 days")


async def run_safe(account: Account):
    async with semaphore:
        await Bot(account).start()


async def run_get_tree_info_module(account: Account) -> tuple[Any, bool | str]:
    async with semaphore:
        client = Bot(account)
        tree_id = await client.process_get_tree_id()
        if tree_id:
            logger.info(f"Account: {account.auth_token} | Tree ID: {tree_id}")
            return client.keypair.address, tree_id


async def run():
    while True:
        Console().build()

        if config.module in (
            "bridge",
            "rewards",
            "tasks",
            "fix_sign",
            "mint_comm_nft",
            "only_rewards",
            "mint_omnihub",
            "mint_make_nft_great_again",
            "mint_summer_nft",
            "mint_flag",
            "mint_shop",
            "mint_air3",
            "mint_supermint",
            "comet_bridge",
            "mint_all_nfts",
            "mint_owlto_summer_nft",
            "mint_omnihub_summer_nft",
            "mint_random_all_nfts",
            "mint_vip3_nft",
            "mint_green_id",
        ):
            tasks = [
                asyncio.create_task(run_safe(account)) for account in config.accounts
            ]
            await asyncio.gather(*tasks)

        elif config.module == "export_trees_ids":
            tasks = [
                asyncio.create_task(run_get_tree_info_module(account))
                for account in config.accounts
            ]
            results = await asyncio.gather(*tasks)
            export_trees_ids(results)

        input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    setup()
    asyncio.run(run())
