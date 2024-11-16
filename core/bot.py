import asyncio
import random
from typing import Any

from models import Account
from loguru import logger
from loader import config

from .api import MintChainAPI
from .exceptions.base import APIError, StealEnergyError
from .modules import CometBridge


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

            except APIError as error:
                logger.error(
                    f"Account: {self.account.auth_token} | {error_message}: {error}"
                )
                return False
            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | {error_message}: {error} | {'Retrying..' if retries > 0 else ''}"
                )
                await asyncio.sleep(delay)
                continue

        return False

    async def process_login(self) -> bool:
        logger.info(f"Account: {self.account.auth_token} | Logging in..")
        return await self.safe_operation(
            operation=self.login,
            success_message="Logged in",
            error_message="Failed to login",
            retries=3,
        )

    async def process_fix_sign(self) -> bool:
        return await self.safe_operation(
            operation=self.fix_sign,
            success_message="Fixed sign",
            error_message="Failed to fix sign",
            retries=2,
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

                amount = int(
                    balance * (config.spin_turntable_by_percentage_of_energy / 100)
                )
                number_of_spins = int(amount // 300)
                if number_of_spins > 5:
                    number_of_spins = 5

                for _ in range(number_of_spins):
                    turntable_proof = await self.get_turntable_forest_proof()
                    status, transaction_hash = await self.claim_onchain(turntable_proof)

                    if status:
                        logger.success(
                            f"Account: {self.account.auth_token} | Spun turntable | Reward: {turntable_proof['energy']} | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )
                    else:
                        logger.error(
                            f"Account: {self.account.auth_token} | Failed to spin turntable | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )

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

    async def process_join_airdrop(self) -> None:
        try:
            await self.join_airdrop()

        except APIError as error:
            logger.error(
                f"Account: {self.account.auth_token} | Failed to join airdrop: {error}"
            )
            return

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Failed to join airdrop: {error}"
            )



    async def process_claim_points_onchain(self) -> bool:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Claiming points on-chain..")

            points_proof = await self.get_points_forest_proof()
            status, transaction_hash = await self.claim_onchain(points_proof)

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Claimed points on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to claim points on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

            referral_proof = await self.get_referral_points_forest_proof()
            if referral_proof["energy"] > 0:
                status, transaction_hash = await self.claim_onchain(referral_proof)

                if status:
                    logger.success(
                        f"Account: {self.account.auth_token} | Claimed referral points on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                    )
                    return True
                else:
                    logger.error(
                        f"Account: {self.account.auth_token} | Failed to claim referral points on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                    )

            if status:
                return True

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

        return False


    async def process_claim_boxes_onchain(self) -> bool:
        try:
            await self.check_balance()
            boxes = await self.get_boxes()
            if boxes:
                logger.info(f"Account: {self.account.auth_token} | Claiming boxes on-chain..")

                for box_id in boxes:
                    box_proof = await self.get_box_forest_proof(str(box_id))
                    status, transaction_hash = await self.claim_onchain(box_proof)

                    if status:
                        logger.success(
                            f"Account: {self.account.auth_token} | Claimed boxes on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )
                    else:
                        logger.error(
                            f"Account: {self.account.auth_token} | Failed to claim boxes on-chain | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )
            else:
                logger.info(f"Account: {self.account.auth_token} | No boxes to claim..")

            return True

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

        return False

    async def process_comet_bridge(self) -> None:
        try:
            amount_to_bridge = round(random.uniform(
                config.comet_bridge_amount_min, config.comet_bridge_amount_max
            ), 10)
            client = CometBridge(
                amount_to_bridge=amount_to_bridge,
                to_address=self.keypair.address,
                mnemonic=config.comet_bridge_wallet,
                rpc_url=config.op_rpc_url,
            )

            logger.info(
                f"Account: {self.account.auth_token} | Bridging {amount_to_bridge} ETH to MINT (via Comet)"
            )
            transaction = await client.build_bridge_transaction()
            status, tx_hash = await client.send_and_verify_transaction(transaction)

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Bridged {amount_to_bridge} ETH to MINT | Transaction: https://optimistic.etherscan.io/tx{tx_hash}"
                )

            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to bridge {amount_to_bridge} ETH to MINT | Transaction: https://optimistic.etherscan.io/tx{tx_hash}"
                )

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Error while bridging: {error}"
            )

    async def process_get_tree_id(self) -> bool | str:
        for _ in range(2):
            try:
                user_info = await self.user_info()
                return str(user_info.treeId)

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to get tree id: {error} | Retrying.."
                )
                await asyncio.sleep(1)

        logger.error(
            f"Account: {self.account.auth_token} | Failed to get tree id after 2 retries | Skipping.."
        )
        return False

    async def process_mint_green_id(self) -> bool:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting Green ID..")

            tree_id = await self.process_get_tree_id()
            if not tree_id:
                return False

            transaction = await self.build_green_id_nft_transaction(int(tree_id))
            status, transaction_hash = await self.send_and_verify_transaction(transaction)

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Green ID | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
                return True
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Green ID | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

        return False


    async def process_steal_energy(self, tree_id: str) -> bool:
        for _ in range(2):
            try:
                user_info = await self.user_info(tree_id=tree_id)
                if not user_info:
                    return False

                energy_list = await self.get_energy_list(user_id=str(user_info.id).strip())
                if energy_list.result:
                    steal_proof = await self.get_steal_energy_forest_proof(user_id=str(user_info.id).strip())
                    status, transaction_hash = await self.claim_onchain(steal_proof)

                    if status:
                        logger.success(
                            f"Account: {self.account.auth_token} | Stolen energy from {user_info.address} | Tree: {tree_id} | Energy: {energy_list.result[0].amount} | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )
                        return True

                    else:
                        logger.error(
                            f"Account: {self.account.auth_token} | Failed to steal energy from {user_info.address} | Tree: {tree_id} | Energy: {energy_list.result[0].amount} | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                        )
                        return False

                else:
                    logger.warning(
                        f"Account: {self.account.auth_token} | Energy not stealable from tree: {tree_id}"
                    )
                    return False

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to steal energy: {error} | Retrying.."
                )
                await asyncio.sleep(1)

        logger.error(f"Account: {self.account.auth_token} | Failed to steal energy after 2 retries | Skipping..")
        raise StealEnergyError()


    async def start(self):
        random_delay = random.randint(
            config.min_delay_before_start, config.max_delay_before_start
        )
        logger.info(
            f"Account: {self.account.auth_token} | Work will start in {random_delay} seconds.."
        )

        await asyncio.sleep(random_delay)

        operations_dict = {
            "fix_sign": [self.process_login, self.process_fix_sign],
            "claim_boxes_onchain": [self.process_login, self.process_claim_boxes_onchain, self.process_show_user_info],
            "claim_points_onchain_and_inject": [self.process_login, self.process_claim_points_onchain, self.process_inject, self.process_show_user_info],
            "spin_turntable_onchain": [self.process_login, self.process_spin_turntable, self.process_show_user_info],
            "comet_bridge_onchain": [self.process_comet_bridge],
            "mint_green_id_nft": [self.process_login, self.process_mint_green_id],
        }

        operations = operations_dict[config.module]

        try:
            for operation in operations:
                if not await operation():
                    break

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Unhandled error: {error}"
            )
        finally:
            logger.success(f"Account: {self.account.auth_token} | Finished")
