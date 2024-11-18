import asyncio

from models import Config
from utils import load_config, AccountProgress

config: Config = load_config()
semaphore = asyncio.Semaphore(config.threads)
progress = AccountProgress(0)
progress.total = len(config.accounts)
