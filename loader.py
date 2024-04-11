import asyncio

from models import Config
from config import load_config

config: Config = load_config()
semaphore = asyncio.Semaphore(config.threads)
