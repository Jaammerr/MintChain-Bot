import asyncio
import random
from typing import Any

from models import Account
from loguru import logger
from loader import config

from .api import MintChainAPI
from .exceptions.base import APIError
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

    # ------------------------
    # Start Upgrade from Mr. X
    # ------------------------

    async def process_spin_turntable(self) -> bool:
        if config.spin_turntable_by_percentage_of_energy > 0:
            try:
                
                if await self.human_balance() < 0.00005:
                    raise Exception(
                        "Insufficient balance to turntable transaction | Required: 0.00005 ETH"
                    )
                
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
                    status, tx_hash, amount = await self.get_forest_proof_and_send_transaction('Turntable')

                    if status:
                        logger.success(
                            f"Account: {self.account.auth_token} | Opened turntable | Reward: {amount} | Transaction: {tx_hash}"
                        )
                        await asyncio.sleep(3)

            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to spin turntable: {error}"
                )

        return True
    
    # ------------------------
    # End Upgrade from Mr. X
    # ------------------------

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

    async def process_mint_comm_nft(self) -> None:
        try:
            await self.check_balance()

            try:
                await self.join_airdrop()
            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to join airdrop: {error}"
                )

            logger.info(
                f"Account: {self.account.auth_token} | Minting commemorative NFT.."
            )
            status, transaction_hash = await self.mint_commemorative_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted commemorative NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint commemorative NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_make_nft_great_again(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting MNGA NFT..")
            status, transaction_hash = await self.mint_make_nft_great_again()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted MNGA NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint MNGA NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_flag_nft(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting Flag NFT..")
            status, transaction_hash = await self.mint_flag_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Flag NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Flag NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_supermint_nft(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting SuperMint NFT..")
            status, transaction_hash = await self.mint_supermint_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted SuperMint NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint SuperMint NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_air3_nft(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting Air3 NFT..")
            status, transaction_hash = await self.mint_air3_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Air3 NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Air3 NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_shop_nft(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting Shop NFT..")
            status, transaction_hash = await self.mint_shop_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Shop NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Shop NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

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

    async def process_mint_vip3_nft(self) -> None:
        try:
            await self.check_balance()

            try:
                await self.join_airdrop()
            except Exception as error:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to join airdrop: {error}"
                )

            logger.info(f"Account: {self.account.auth_token} | Minting VIP3 NFT..")
            status, transaction_hash = await self.mint_vip3_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted VIP3 NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint VIP3 NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_green_id(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting Green ID..")

            tree_id = await self.process_get_tree_id()
            if not tree_id:
                return

            status, transaction_hash = await self.mint_green_id_nft(int(tree_id))

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Green ID | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Green ID | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")


    async def process_mint_gainfi_nft(self) -> None:
        try:
            await self.check_balance()
            logger.info(f"Account: {self.account.auth_token} | Minting GainFi NFT..")
            status, transaction_hash = await self.mint_gainfi_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted GainFi NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint GainFi NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    # async def process_mint_omnihub_collection(self) -> None:
    #     try:
    #         if await self.human_balance() < 0.0001:
    #             raise Exception("Insufficient balance to mint OmniHub collection | Required: 0.0001 ETH")
    #
    #         logger.info(f"Account: {self.account.auth_token} | Minting OmniHub collection")
    #         status, transaction_hash = await self.mint_omnihub_collection()
    #
    #         if status:
    #             logger.success(
    #                 f"Account: {self.account.auth_token} | Minted OmniHub collection | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
    #             )
    #         else:
    #             logger.error(
    #                 f"Account: {self.account.auth_token} | Failed to mint OmniHub collection | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
    #             )
    #
    #     except Exception as error:
    #         logger.error(
    #             f"Account: {self.account.auth_token} | {error}"
    #         )

    async def process_mint_summer_nft(self) -> None:
        try:
            if await self.human_balance() < 0.0001:
                raise Exception(
                    "Insufficient balance to mint Summer NFT | Required: 0.0001 ETH"
                )

            logger.info(f"Account: {self.account.auth_token} | Minting Summer NFT..")
            status, transaction_hash = await self.mint_summer_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Summer NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Summer NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_owlto_summer_fest_nft(self) -> None:
        try:
            if await self.human_balance() < 0.0001:
                raise Exception(
                    "Insufficient balance to mint Owlto Summer Fest NFT | Required: 0.0001 ETH"
                )

            logger.info(
                f"Account: {self.account.auth_token} | Minting Owlto Summer Fest NFT.."
            )
            status, transaction_hash = await self.mint_owlto_summer_fest_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted Owlto Summer Fest NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint Owlto Summer Fest NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_mint_omnihub_summer_nft(self) -> None:
        try:
            if await self.human_balance() < 0.0001:
                raise Exception(
                    "Insufficient balance to mint OmniHub Summer NFT | Required: 0.0001 ETH"
                )

            logger.info(
                f"Account: {self.account.auth_token} | Minting OmniHub Summer NFT.."
            )
            status, transaction_hash = await self.mint_omnihub_summer_fest_nft()

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Minted OmniHub Summer NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to mint OmniHub Summer NFT | Transaction: https://explorer.mintchain.io/tx/{transaction_hash}"
                )

        except Exception as error:
            logger.error(f"Account: {self.account.auth_token} | {error}")

    async def process_comet_bridge(self) -> None:
        try:
            amount_to_bridge = random.uniform(
                config.comet_bridge_amount_min, config.comet_bridge_amount_max
            )
            client = CometBridge(
                amount_to_bridge=amount_to_bridge,
                to_address=self.keypair.address,
                mnemonic=config.comet_bridge_wallet,
                rpc_url=config.arb_rpc_url,
            )

            logger.info(
                f"Account: {self.account.auth_token} | Bridging {amount_to_bridge} ETH to MINT (via Comet)"
            )
            transaction = await client.build_bridge_transaction()
            status, tx_hash = await client.send_and_verify_transaction(transaction)

            if status:
                logger.success(
                    f"Account: {self.account.auth_token} | Bridged {amount_to_bridge} ETH to MINT | Transaction: https://arbiscan.io/tx/{tx_hash}"
                )

            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to bridge {amount_to_bridge} ETH to MINT | Transaction: https://arbiscan.io/tx/{tx_hash}"
                )

        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Error while bridging: {error}"
            )

    async def process_complete_tasks(self):
        return await self.safe_operation(
            operation=self.complete_tasks,
            success_message="Finished completing tasks",
            error_message="Failed to complete tasks",
            delay=10,
            retries=3,
        )

    async def process_get_tree_id(self) -> bool | str:
        for _ in range(2):
            try:
                if not await self.process_login():
                    return False

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

    async def process_mint_random_all_nfts(self) -> None:
        operations_dict = {
            "mint_comm_nft": self.process_mint_comm_nft,
            "mint_make_nft_great_again": self.process_mint_make_nft_great_again,
            "mint_flag": self.process_mint_flag_nft,
            "mint_shop": self.process_mint_shop_nft,
            "mint_air3": self.process_mint_air3_nft,
            "mint_supermint": self.process_mint_supermint_nft,
            "mint_summer_nft": self.process_mint_summer_nft,
            "mint_owlto_summer_nft": self.process_mint_owlto_summer_fest_nft,
            "mint_omnihub_summer_nft": self.process_mint_omnihub_summer_nft,
            "mint_vip3_nft": self.process_mint_vip3_nft,
            "mint_green_id": self.process_mint_green_id,
        }

        mint_modules = config.mint_random_all_nfts
        random.shuffle(mint_modules)

        for module in mint_modules:
            operation = operations_dict.get(module)
            if operation:
                try:
                    await operation()
                except Exception as error:
                    logger.error(
                        f"Account: {self.account.auth_token} | Failed to process {module}: {error}"
                    )
                finally:
                    delay = random.randint(
                        config.delay_between_mint_min, config.delay_between_mint_max
                    )
                    logger.debug(
                        f"Account: {self.account.auth_token} | Sleeping for {delay} seconds.."
                    )
                    await asyncio.sleep(delay)

    # ------------------------
    # Start Upgrade from Mr. X
    # ------------------------

    async def process_total_user(self) -> bool | int:
        try:
            if not await self.process_login():
                return False
            
            total_user = await self.total_user()

            if total_user:
                logger.success(
                    f"Account: {self.account.auth_token} | Success get total users | Total users: {total_user}"
                )
                return total_user
            
        except Exception as error:
            logger.error(
                f"Account: {self.account.auth_token} | Failed to get total users: {error} | Retrying.."
            )
            await asyncio.sleep(1)

    async def process_find_and_steal_rewards(self, start: int, end: int, min_amount: int = None):
        try:

            if not await self.process_login():
                return False
            
            if not min_amount:
                min_amount = 0
            
            logger.debug(
                f"Account: {self.account.auth_token} | Begin the search for energy on trees in the range | Range: {start}, {end}"
            )


            for i in range(start, end):

                if await self.human_balance() < 0.00005:
                    raise Exception(
                        "Insufficient balance to steal transaction | Required: 0.00005 ETH"
                    )
                
                tree_id = i
                other_user_info = await self.user_info(tree_id)

                if other_user_info:
                    other_user_energy = await self.get_energy_list(str(other_user_info.id))
                    if other_user_energy.result:
                        for energy in other_user_energy.result:
                            if energy.stealable and energy.amount >= min_amount:

                                logger.debug(
                                    f"Account: {self.account.auth_token} | Find other trees user reward | Tree: {tree_id} | Amount: {energy.amount}"
                                )

                                status, tx_hash, amount = await self.get_forest_proof_and_send_transaction('Steal', user_id = other_user_info.id)
                                if status:
                                    logger.success(
                                        f"Account: {self.account.auth_token} | Steal other trees user reward | Tree: {tree_id} | Amount: {amount} | Transaction: https://explorer.mintchain.io/tx/{tx_hash}"
                                    )

                await asyncio.sleep(0.5)

        except Exception as error:

            if "Invalid User" in str(error) or "No Data" in str(error):
                logger.warning(
                    f"Account: {self.account.auth_token} | Warning Invalid User or No data: {error}"
                )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Failed to find other trees rewards: {error}"
                )
                await asyncio.sleep(1)

    # ------------------------
    # End Upgrade from Mr. X
    # ------------------------ 

    async def start(self):
        random_delay = random.randint(
            config.min_delay_before_start, config.max_delay_before_start
        )
        logger.info(
            f"Account: {self.account.auth_token} | Work will start in {random_delay} seconds.."
        )
        await asyncio.sleep(random_delay)

        operations_dict = {
            "rewards": [
                self.process_login,
                self.process_claim_daily_reward,
                self.process_spin_turntable,
                self.process_inject,
                self.process_show_user_info,
            ],
            "only_rewards": [
                self.process_login,
                self.process_claim_daily_reward,
                self.process_show_user_info,
            ],
            "fix_sign": [self.process_login, self.process_fix_sign],
            "mint_comm_nft": [self.process_mint_comm_nft],
            "mint_make_nft_great_again": [self.process_mint_make_nft_great_again],
            "mint_summer_nft": [self.process_mint_summer_nft],
            "mint_flag": [self.process_mint_flag_nft],
            "mint_shop": [self.process_mint_shop_nft],
            "mint_air3": [self.process_mint_air3_nft],
            "mint_supermint": [self.process_mint_supermint_nft],
            "comet_bridge": [self.process_comet_bridge],
            "mint_random_all_nfts": [self.process_mint_random_all_nfts],
            "mint_owlto_summer_nft": [self.process_mint_owlto_summer_fest_nft],
            "mint_omnihub_summer_nft": [self.process_mint_omnihub_summer_nft],
            "mint_vip3_nft": [self.process_mint_vip3_nft],
            "tasks": [self.process_login, self.process_complete_tasks],
            "mint_gainfi_nft": [self.process_mint_gainfi_nft],
            "default": [self.process_login, self.process_complete_tasks],
        }

        operations = operations_dict.get(config.module, operations_dict["default"])

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
