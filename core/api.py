import asyncio
import random

import httpx
import pyuseragents
import names

from typing import Literal, List
from noble_tls import Session, Client
from Jam_Twitter_API.account_async import TwitterAccountAsync

from models import *
from loader import config as configuration
from .modules.gainfi_api import GainfiAPI
from .modules.temp_mail import TempMail

from .wallet import Wallet
from .modules import *
from .exceptions.base import APIError


class MintChainAPI(Wallet):
    API_URL = "https://www.mintchain.io/api"

    def __init__(self, account_data: Account):
        super().__init__(
            mnemonic=account_data.pk_or_mnemonic, rpc_url=configuration.mint_rpc_url
        )
        self.account = account_data
        self.session = self.setup_session()
        self.twitter_account: TwitterAccountAsync = None  # type: ignore

    @property
    def jwt_token(self) -> str:
        return self.session.headers["authorization"].replace("Bearer ", "")

    @property
    async def energy_balance(self) -> int:
        return (await self.user_info()).energy

    @property
    async def tree_size(self) -> int:
        return (await self.user_info()).tree

    @property
    async def rank(self) -> int:
        return (await self.rank_info()).rank

    def setup_session(self) -> Session:
        session = Session(client=Client.CHROME_120)
        session.random_tls_extension_order = True

        session.timeout_seconds = 15
        session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "referer": "https://www.mintchain.io",
            "user-agent": pyuseragents.random(),
        }
        session.proxies = {
            "http": self.account.proxy,
            "https": self.account.proxy,
        }
        return session

    async def send_request(
        self,
        request_type: Literal["POST", "GET"] = "POST",
        method: str = None,
        json_data: dict = None,
        params: dict = None,
        url: str = None,
        headers: dict = None,
        verify: bool = True,
    ):
        def _verify_response(_response: dict) -> dict:
            if "code" in _response:
                if _response["code"] not in (10000, 200):
                    raise APIError(
                        f"{_response.get('msg')} | Method: {method} | URL: {url}"
                    )

                return _response

        if request_type == "POST":
            if not url:
                response = await self.session.post(
                    f"{self.API_URL}{method}",
                    json=json_data,
                    params=params,
                    headers=headers,
                )

            else:
                response = await self.session.post(
                    url, json=json_data, params=params, headers=headers
                )

        else:
            if not url:
                response = await self.session.get(
                    f"{self.API_URL}{method}", params=params, headers=headers
                )

            else:
                response = await self.session.get(url, params=params, headers=headers)

        response.raise_for_status()
        if verify:
            return _verify_response(response.json())
        else:
            return response.json()

    async def is_daily_reward_claimed(self) -> bool:
        response = await self.send_request(
            request_type="GET", method="/tree/energy-list"
        )
        return response["result"][-1]["freeze"]

    async def green_id(self) -> dict:
        response = await self.send_request(request_type="GET", method="/tree/green-id")
        return response

    async def get_energy_list(self, user_id: str = None) -> EnergyListData:
        if not user_id:
            response = await self.send_request(
                request_type="GET", method="/tree/energy-list"
            )
        else:
            response = await self.send_request(
                request_type="GET",
                method="/tree/steal/energy-list",
                params={"id": user_id},
            )

            if (
                response
                and response.get("msg", "")
                == "You are too late, the energy has already been collected by its owner."
            ):
                return EnergyListData(result=[])

        return EnergyListData(**response)

    async def get_task_list(self) -> TaskListData:
        response = await self.send_request(
            request_type="GET", method=f"/tree/task-list?address={self.keypair.address}"
        )
        return TaskListData(**response)

    async def complete_tasks(self):
        task_list = await self.get_task_list()
        for task in task_list.result:
            if task.spec not in ("discord-follow", "stake"):
                if task.claimed:
                    logger.debug(
                        f"Account: {self.account.auth_token} | Task already completed: {task.name}"
                    )
                    continue

                try:
                    if task.spec in ("twitter-post", "twitter-follow"):
                        if not self.twitter_account:
                            self.load_twitter_account()

                        if task.spec == "twitter-follow":
                            user_id = self.twitter_account.get_user_id(
                                "Mint_Blockchain"
                            )
                            self.twitter_account.follow(user_id)
                            await self.submit_task_id(task.id)

                        else:
                            tweet_text = "I'm collecting @Mint_Blockchain's ME $MINT in the #MintForest🌳!\n\nMint is the L2 for NFT industry, powered by @nftscan_com and @Optimism.\n\nJoin Mint Forest here: https://mintchain.io/mint-forest\n\n#MintBlockchain #L2forNFT"

                            data = self.twitter_account.tweet(tweet_text)
                            tweet_url = f'https://x.com/JammerCrypto/status/{data["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]}'
                            await self.submit_task_id(task.id, twitter_post=tweet_url)

                    else:
                        await self.submit_task_id(task.id)

                    logger.debug(
                        f"Account: {self.account.auth_token} | Task completed: {task.name} | Reward: {task.amount} energy"
                    )
                    await asyncio.sleep(3)

                except APIError as error:
                    logger.error(
                        f"Account: {self.account.auth_token} | Failed to complete task: {task.name} | {error}"
                    )
                    await asyncio.sleep(3)

    async def claim_daily_rewards(self) -> None:
        energy_list = await self.get_energy_list()
        for energy in energy_list.result:
            json_data = {
                "uid": energy.uid,
                "amount": energy.amount,
                "includes": energy.includes,
                "type": energy.type,
                "id": energy.id,
            }

            if energy.type == "daily":
                if energy.freeze:
                    logger.debug(
                        f"Account: {self.account.auth_token} | Daily reward already claimed"
                    )
                    continue
                else:
                    json_data["freeze"] = energy.freeze

            # ------------------------
            # Start Upgrade from Mr. X
            # ------------------------

            if await self.human_balance() > 0.00005:
                status, tx_hash, amount = await self.get_forest_proof_and_send_transaction('Signin')
                if status:
                    logger.success(
                        f"Account: {self.account.auth_token} | Claimed signin double daily reward | Amount: {amount} | Transaction: {tx_hash}"
                    )
            else:
                logger.error(
                    f"Account: {self.account.auth_token} | Insufficient balance to double signin transaction | Required: 0.00005 ETH"
                )

                await self.send_request(method="/tree/claim", json_data=json_data)
                logger.debug(
                    f"Account: {self.account.auth_token} | Claimed {energy.amount} energy | Type: {energy.type}"
                )

            # ------------------------
            # End Upgrade from Mr. X
            # ------------------------

            await asyncio.sleep(1)

        await self.claim_boxes()

    async def bind_invite_code(self) -> ResponseData:
        jwt_token = self.jwt_token

        session = Session(client=Client.CHROME_120)
        session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "sk-SK,sk;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": "Bearer",
            "referer": "https://www.mintchain.io/mint-forest",
            "user-agent": self.session.headers["user-agent"],
        }

        json_data = {
            "code": str(configuration.referral_code),
            "jwtToken": jwt_token,
        }

        response = await session.get(
            "https://www.mintchain.io/api/tree/invitation", params=json_data
        )
        return ResponseData(**response.json())

    async def load_twitter_account(self) -> None:
        self.twitter_account = await TwitterAccountAsync.run(
            auth_token=self.account.auth_token,
            setup_session=True,
            proxy=self.account.proxy,
        )

    async def connect_twitter(self) -> dict:
        params = {
            "code_challenge": "mintchain",
            "code_challenge_method": "plain",
            "client_id": "enpfUjhndkdrdHhld29aTW96eGM6MTpjaQ",
            "redirect_uri": "https://www.mintchain.io/mint-forest",
            "response_type": "code",
            "scope": "tweet.read users.read follows.read offline.access",
            "state": "mintchain",
        }

        if not self.twitter_account:
            await self.load_twitter_account()

        approved_code = await self.twitter_account.bind_account_v2(params)

        params = {
            "code": approved_code,
            "jwtToken": self.jwt_token,
            "address": self.keypair.address,
        }
        response = await self.send_request(
            url="https://www.mintchain.io/api/twitter/verify", params=params
        )
        return response

    async def rank_info(self) -> RankData:
        response = await self.send_request(request_type="GET", method="/tree/me-rank")
        return RankData(**response["result"])

    async def user_info(self, tree_id: str = None) -> UserInfo:
        if not tree_id:
            response = await self.send_request(
                request_type="GET", method="/tree/user-info"
            )
        else:
            response = await self.send_request(
                request_type="GET", method="/tree/user-info", params={"treeid": tree_id}
            )

        return UserInfo(**response["result"])

    async def assets(self) -> List[AssetData]:
        response = await self.send_request(request_type="GET", method="/tree/asset")
        return [AssetData(**data) for data in response["result"]]
    
    # ------------------------
    # Start Upgrade from Mr. X
    # ------------------------

    async def claim_boxes(self):
        assets = await self.assets()
        for asset in assets:
            if not asset.createdAt:
                if await self.human_balance() > 0.00005:
                    status, tx_hash, amount = await self.get_forest_proof_and_send_transaction('OpenReward', box_id = asset.id)
                    if status:
                        logger.success(
                            f"Account: {self.account.auth_token} | Box opened reward | Amount: {amount} | Transaction: https://explorer.mintchain.io/tx/{tx_hash}"
                        )
                else:
                    logger.error(
                        f"Account: {self.account.auth_token} | Insufficient balance to openreward transaction | Required: 0.00005 ETH"
                    )

            await asyncio.sleep(1)

    # ------------------------
    # End Upgrade from Mr. X
    # ------------------------

    async def inject(self, amount: int = None) -> InjectData:
        if not amount:
            amount = await self.energy_balance

        if amount <= 0:
            return InjectData(code=0, result=False, msg="Energy balance is 0")

        json_data = {
            "address": self.keypair.address,
            "energy": amount,
        }

        response = await self.send_request(method="/tree/inject", json_data=json_data)
        return InjectData(**response)

    async def fix_sign(self) -> None:
        await self.send_request(request_type="GET", method="/tree/fix-sign")

    async def submit_task_id(self, task_id: int, twitter_post: str = None) -> None:
        json_data = {
            "id": task_id,
        }

        if twitter_post:
            json_data["twitterurl"] = twitter_post

        await self.send_request(method="/tree/task-submit", json_data=json_data)

    async def get_make_nft_great_again_proofs(self) -> list[str]:
        params = {
            "user": self.keypair.address,
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "priority": "u=1, i",
            "referer": "https://mn-ga.com/?allow=true",
            "user-agent": self.session.headers["user-agent"],
        }

        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(
                "https://mn-ga.com/api/reward/nft-proof", params=params
            )
            response = response.json()
            return response["msg"]["proof"]

    async def mint_commemorative_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_commemorative_nft_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint commemorative NFT: {error}")

    async def mint_flag_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_mint_flag_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Flag NFT: {error}")

    async def mint_shop_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_mint_shop_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Shop NFT: {error}")

    async def mint_air3_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_mint_air3_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Air3 NFT: {error}")

    async def mint_green_id_nft(self, tree_id: int) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_green_id_nft_transaction(tree_id)
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Green ID NFT: {error}")

    async def mint_vip3_nft(self) -> tuple[bool | Any, str]:
        try:
            client = Vip3API(self.account)
            await client.login()
            mint_data = await client.get_mint_data()
            transaction = await self.build_vip3_nft_transaction(mint_data)

            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint VIP3 NFT: {error}")

    async def mint_supermint_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_mint_supermint_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint SuperMint NFT: {error}")

    async def mint_summer_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_summer_nft_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Summer NFT: {error}")

    async def mint_make_nft_great_again(self) -> tuple[bool | Any, str]:
        try:
            proofs = await self.get_make_nft_great_again_proofs()
            transaction = await self.build_make_nft_great_again_transaction(
                proofs=proofs
            )

            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Make NFT Great Again: {error}")

    async def mint_createx_collection(self) -> tuple[bool | Any, str]:
        try:
            name = f"{names.get_first_name()} {names.get_last_name()}"
            symbol = random.choice(
                [f"{name[:3].upper()}", f"{name[:4].upper()}", f"{name[:5].upper()}"]
            )
            description = f"Collection of {name} NFTs"
            price = random.uniform(0.00001, 0.05)
            royalty_fee = random.randint(1, 50)

            client = CreateXAPI(
                mnemonic=self.account.pk_or_mnemonic, rpc_url=configuration.mint_rpc_url
            )
            await client.login()
            collection_id = await client.create_collection(
                name=name,
                symbol=symbol,
                description=description,
                price=str(price),
                royalty_fee=str(royalty_fee),
            )
            await client.create_query_collection(collection_id=collection_id)
            trx_data = await client.deploy(collection_id=collection_id)

            transaction = await self.build_createx_collection_transaction(trx_data)
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint OmniHub collection: {error}")


    async def mint_gainfi_nft(self):
        for _ in range(3):
            try:
                temp_mail = TempMail()
                await temp_mail.generate_account()

                client = GainfiAPI(self.account)
                await client.login()

                await client.send_email_code(temp_mail.account.address)
                logger.info(f"Account: {self.account.auth_token} | Waiting for verification code")
                code = await temp_mail.get_verification_code()
                mint_data = await client.verify_email(temp_mail.account.address, code)
                logger.info(f"Account: {self.account.auth_token} | Code approved | Minting GainFi NFT..")

                transaction = await self.build_gainfi_mint_transaction(mint_data)
                status, tx_hash = await self.send_and_verify_transaction(transaction)
                return status, tx_hash

            except APIError as error:
                if "Visit too frequently" in str(error):
                    logger.error(f"Account: {self.account.auth_token} | Visit too frequently | Retrying..")
                    await asyncio.sleep(3)

            except Exception as error:
                raise Exception(f"Failed to mint GainFi NFT: {error}")

            finally:
                await temp_mail.session.close()

        logger.error(f"Account: {self.account.auth_token} | Failed to mint GainFi NFT")

    async def mint_owlto_summer_fest_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_owlto_summer_fest_nft_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint Owlto Summer Fest NFT: {error}")

    async def mint_omnihub_summer_fest_nft(self) -> tuple[bool | Any, str]:
        try:
            transaction = await self.build_omnihub_summer_fest_nft_transaction()
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to mint OmniHub Summer Fest NFT: {error}")

    async def verify_wallet(self) -> ResponseData:
        json_data = {
            "jwtToken": self.jwt_token,
        }

        response = await self.send_request(method="/wallet/verify", json_data=json_data)
        return ResponseData(**response)

    async def join_airdrop(self) -> dict:
        messages = self.sign_mint_message("airdrop")

        params = {
            "wallet_address": self.keypair.address,
            "signature": messages.signed_message,
            "message": messages.message,
            "invite_code": "",
        }

        return await self.send_request(
            request_type="GET",
            url="https://mpapi.mintchain.io/api/user/sign",
            params=params,
        )
    
    # ------------------------
    # Start Upgrade from Mr. X
    # ------------------------

    async def total_user(self):
        response = await self.send_request(request_type="GET", method="/tree/total-user")
        return response['result']
    
    async def get_forest_proof_and_send_transaction(self, type: str, user_id: int = None, box_id: int = None):

        try:
            
            params = {
                "type": type,
            }

            params_types = {
                'Steal': {'id': user_id},
                'OpenReward': {'boxId': box_id}
            }
            
            params.update(params_types.get(type, {}))

            response = await self.send_request(method="/tree/get-forest-proof", request_type = "GET", params = params)
            data = response['result']['tx']

            if type == 'Steal':
                amount = response['result'].get('amount')
            else:
                amount = response['result'].get('energy')

            if data:

                contract = "0x12906892AaA384ad59F2c431867af6632c68100a" # Mint Forest contact: https://explorer.mintchain.io/address/0x12906892AaA384ad59F2c431867af6632c68100a
                transaction = {
                    "from": self.keypair.address,
                    "to": contract,
                    "gasPrice": await self.eth.gas_price,
                    "nonce": await self.transactions_count(),
                    "gas": int(await self.eth.estimate_gas({
                        "from": self.keypair.address,
                        "to": contract,
                        "data": data
                    }) * 1.2),
                    "data": data
                }

                status, tx_hash = await self.send_and_verify_transaction(transaction)
                return status, tx_hash, amount
            
        except Exception as error:
            raise Exception(f"Failed get forest proof and send transaction: {error}")
        
    # ------------------------
    # End Upgrade from Mr. X
    # ------------------------

    async def login(self):
        messages = self.sign_mint_message("forest")

        json_data = {
            "address": self.keypair.address,
            "signature": messages.signed_message,
            "message": messages.message,
        }

        response = await self.send_request(method="/tree/login", json_data=json_data)
        data = LoginWalletData(**response["result"])
        self.session.headers["authorization"] = f"Bearer {data.access_token}"

        if data.user.status == "pending":
            await self.verify_wallet()

        if not data.user.twitter:
            await self.connect_twitter()
            logger.debug(
                f"Account: {self.account.auth_token} | Twitter account connected"
            )

        if not data.user.inviteId:
            await self.bind_invite_code()
            logger.debug(f"Account: {self.account.auth_token} | Referral code bound")

        await self.green_id()
        await self.assets()
        await self.rank_info()
        await self.user_info()
        await self.get_energy_list()
