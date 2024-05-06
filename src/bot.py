import asyncio
import random
from typing import Any

from models import Account
from loguru import logger
from loader import config

from .api import MintChainAPI


class Bot(MintChainAPI):
    def __init__(self, account: Account):
        super().__init__(account_data=account)

    async def safe_operation(
        self,
        operation: callable,
        success_message: str,
        error_message: str,
        retries: int = 0,
        delay: int = 3,
        argument: Any = None,
    ) -> bool:
        for _ in range(retries):
            try:
                await operation() if argument is None else await operation(argument)
                logger.success(
                    f"Account: {self.account.auth_token} | {success_message}"
                )
                return True

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | {error_message}: {error} | {'Retrying..' if retries > 0 else ''}"
                )
                await asyncio.sleep(delay)
                continue

        return False

    async def process_login(self) -> bool:
        return await self.safe_operation(
            operation=self.login,
            success_message="Logged in",
            error_message="Failed to login",
            retries=3,
        )

    async def process_claim_daily_reward(self) -> bool:
        return await self.safe_operation(
            operation=self.claim_daily_rewards,
            success_message="Finished claiming daily rewards",
            error_message="Failed to claim daily rewards",
            delay=10,
            retries=3,
        )

    async def process_inject(self) -> bool:
        return await self.safe_operation(
            operation=self.inject,
            success_message="Finished injecting energy",
            error_message="Failed to inject energy",
            retries=3,
        )

    async def process_spin_turntable(self) -> bool:
        if config.spin_turntable_by_percentage_of_energy > 0:
            try:
                balance = await self.energy_balance
                if balance < 300:
                    logger.warning(
                        f"Account: {self.account.auth_token} | Not enough energy to spin turntable"
                    )
                    return True

                amount = int(balance * (config.spin_turntable_by_percentage_of_energy / 100))
                number_of_spins = int(amount // 300)
                if number_of_spins > 5:
                    number_of_spins = 5

                for _ in range(number_of_spins):
                    reward = await self.spin_turntable()
                    logger.success(f"Account: {self.account.auth_token} | Opened turntable | Reward: {reward.energy} energy")
                    await asyncio.sleep(3)

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to spin turntable: {error}"
                )

        return True



    async def process_show_user_info(self) -> None:
        try:
            info = await self.tree_size
            logger.success(
                f"Account: {self.account.auth_token} | Total injected energy: {info} | Daily actions done.."
            )

        except Exception as error:
            logger.warning(
                f"Account: {self.account.auth_token} | Failed to get user info: {error} | Daily actions done.."
            )

    async def process_testnet_bridge(self) -> bool:
        return await self.safe_operation(
            operation=self.testnet_bridge,
            success_message="Testnet bridge completed",
            error_message="Failed to complete testnet bridge",
            delay=30,
            retries=3,
        )

    async def process_complete_tasks(self):
        return await self.safe_operation(
            operation=self.complete_tasks,
            success_message="Finished completing tasks",
            error_message="Failed to complete tasks",
            delay=10,
            retries=3,
        )

    async def start(self):
        random_delay = random.randint(config.min_delay_before_start, config.max_delay_before_start)
        logger.info(
            f"Account: {self.account.auth_token} | Work will start in {random_delay} seconds.."
        )
        await asyncio.sleep(random_delay)

        try:
            if config.module == "rewards":
                operations = [
                    self.process_login,
                    self.process_claim_daily_reward,
                    self.process_spin_turntable,
                    self.process_inject,
                    self.process_show_user_info,
                ]

            elif config.module == "bridge":
                operations = [
                    self.process_login,
                    self.process_testnet_bridge,
                ]

            else:
                operations = [
                    self.process_login,
                    self.process_complete_tasks,
                ]

            for operation in operations:
                if not await operation():
                    break

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Unhandled error: {error}"
            )

        finally:
            logger.success(
                f"Account: {self.account.auth_token} | Finished"
            )
