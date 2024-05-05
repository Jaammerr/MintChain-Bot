import asyncio
import sys
import urllib3

from loguru import logger

from loader import config, semaphore
from src.bot import Bot
from models import Account
from console import Console


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


async def run():
    while True:
        Console().build()

        tasks = [
            asyncio.create_task(run_safe(account)) for account in config.accounts
        ]
        await asyncio.gather(*tasks)
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    setup()
    asyncio.run(run())
