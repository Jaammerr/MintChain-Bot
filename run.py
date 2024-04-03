import asyncio
import sys
import urllib3
from loguru import logger

from loader import config
from src.bot import Bot
from utils import show_dev_info


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


async def run():
    show_dev_info()
    logger.info(
        f"MintChain Bot started | Version: 1.0 | Total accounts: {len(config.accounts)}\n\n"
    )

    while True:
        logger.info(f"Starting new iteration")
        tasks = [
            asyncio.create_task(Bot(account).start()) for account in config.accounts
        ]

        await asyncio.gather(*tasks)
        logger.debug(
            f"\n\nIteration finished | Sleeping for {config.iteration_delay} hours\n\n"
        )
        await asyncio.sleep(config.iteration_delay * 60 * 60)


if __name__ == "__main__":
    setup()
    asyncio.run(run())
