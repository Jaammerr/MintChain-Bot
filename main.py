import asyncio
import sys
import random
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
        
# ------------------------
# Start Upgrade from Mr. X
# ------------------------

async def run_total_user(account: Account):
    return await Bot(account).process_total_user()

        
async def run_find_and_steal_rewards_module(account: Account, start: int, end: int, min_amount: int = None):
    async with semaphore:
        await Bot(account).process_find_and_steal_rewards(start, end, min_amount)

# ------------------------
# End Upgrade from Mr. X
# ------------------------


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
            "mint_gainfi_nft",
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

        # ------------------------
        # Start Upgrade from Mr. X
        # ------------------------
        
        elif config.module == "total_user":
            return await run_total_user(random.choice(config.accounts))

        elif config.module == "find_and_steal_other_trees_rewards":

            total_user = await run_total_user(random.choice(config.accounts))
            
            min_amount = config.find_and_steal_min_amount
            start_range = int((config.find_and_steal_percentage_range_start / 100) * total_user)
            end_range = int((config.find_and_steal_percentage_range_end / 100) * total_user)

            chunk_size = (end_range - start_range) // len(config.accounts)

            tasks = []

            for i, account in enumerate(config.accounts):

                start = start_range + (i * chunk_size)
                end = start + chunk_size if i < len(config.accounts) - 1 else end_range
                tasks.append(
                    asyncio.create_task(run_find_and_steal_rewards_module(account, start, end, min_amount))
                )

            results = await asyncio.gather(*tasks)

            # ------------------------
            # End Upgrade from Mr. X
            # ------------------------

        input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    setup()
    asyncio.run(run())
