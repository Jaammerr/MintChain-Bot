import asyncio
import sys
from itertools import cycle
from typing import Any

import urllib3


from loguru import logger

from core.exceptions.base import StealEnergyError
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



async def run_steal_energy_module():
    start_number = config.start_stealing_from_tree
    trees_cycle = cycle(range(start_number, -1, -1))

    for account in config.accounts:
        try:
            client = Bot(account)
            status = await client.process_login()
            if not status:
                continue

            for _ in range(8):
                while True:
                    tree_id = str(next(trees_cycle))
                    status = await client.process_steal_energy(tree_id=tree_id)
                    if not status:
                        await asyncio.sleep(0.3)
                    else:
                        break

        except StealEnergyError:
            continue



async def run():
    while True:
        Console().build()

        if config.module in (
            "claim_points_onchain_and_inject",
            "claim_boxes_onchain",
            "spin_turntable_onchain",
            "comet_bridge_onchain",
            "mint_green_id_nft"
        ):
            tasks = [
                asyncio.create_task(run_safe(account)) for account in config.accounts
            ]
            await asyncio.gather(*tasks)

        elif config.module == "steal_energy_onchain":
            await run_steal_energy_module()

        input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    setup()
    asyncio.run(run())
