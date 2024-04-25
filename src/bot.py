import asyncio
import random

from models import Account
from loguru import logger
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
    ) -> bool:
        for _ in range(retries):
            try:
                await operation()
                logger.success(
                    f"Account: {self.account.auth_token} | {success_message}"
                )
                return True

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | {error_message}: {error} | {'Retrying..' if retries > 0 else ''}"
                )
                await asyncio.sleep(1)
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
        return (
            await self.safe_operation(
                operation=self.claim_daily_reward,
                success_message="Daily reward claimed",
                error_message="Failed to claim daily reward",
                retries=3,
            )
            if not await self.is_daily_reward_claimed()
            else logger.success(
                f"Account: {self.account.auth_token} | Daily reward already claimed"
            )
        )

    async def process_inject(self) -> bool:
        return await self.safe_operation(
            operation=self.inject,
            success_message="Energy injected",
            error_message="Failed to inject energy",
            retries=3,
        )

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

    async def process_complete_tasks(self) -> bool:
        return await self.safe_operation(
            operation=self.complete_all_tasks,
            success_message="All tasks have been completed",
            error_message="Failed to complete all tasks",
            retries=3,
        )

    async def start(self):
        random_delay = random.randint(1, 30)
        logger.info(
            f"Account: {self.account.auth_token} | Work will start in {random_delay} seconds.."
        )
        await asyncio.sleep(random_delay)

        try:
            operations = [
                self.process_login,
                self.process_complete_tasks,
                self.process_claim_daily_reward,
                self.process_inject,
                self.process_show_user_info,
            ]

            for operation in operations:
                if not await operation():
                    break

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Unhandled error: {error}"
            )
        finally:
            await self.safe_operation(
                operation=self.update_proxy,
                success_message="Proxy updated",
                error_message="Failed to update proxy",
                retries=3,
            )

            logger.success(
                f"Account: {self.account.auth_token} | Finished | Waiting for next iteration.."
            )
