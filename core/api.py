import asyncio
import random

import httpx
import pyuseragents
import names

from typing import Literal, List
from curl_cffi.requests import AsyncSession
from Jam_Twitter_API.account_async import TwitterAccountAsync

from models import *
from loader import config as configuration, progress
from .modules.gainfi_api import GainfiAPI
from .modules.temp_mail import TempMail

from .wallet import Wallet
from .modules import *
from .exceptions.base import APIError, StealEnergyError


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

    def setup_session(self) -> AsyncSession:
        session = AsyncSession(impersonate="chrome120", verify=False)
        session.random_tls_extension_order = True

        session.timeout_seconds = 15
        session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "referer": "https://www.mintchain.io",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            if task.claimed:
                logger.debug(
                    f"Account: {self.account.auth_token} | Task already completed: {task.name}"
                )
                continue

            try:
                if task.spec not in ("discord-follow", "twitter-follow", "stake") and not task.name.startswith("Share"):
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

        progress.increment()
        return True

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

            await self.send_request(method="/tree/claim", json_data=json_data)
            logger.debug(
                f"Account: {self.account.auth_token} | Claimed {energy.amount} energy | Type: {energy.type}"
            )
            await asyncio.sleep(1)


    async def bind_invite_code(self) -> ResponseData:
        jwt_token = self.jwt_token

        session = AsyncSession(impersonate="chrome120", verify=False)
        session.random_tls_extension_order = True

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

    async def open_box(self, box_id: int) -> OpenBoxData:
        json_data = {
            "boxId": box_id,
        }

        response = await self.send_request(method="/tree/open-box", json_data=json_data)
        return OpenBoxData(**response["result"])

    async def get_boxes(self) -> List[int]:
        assets = await self.assets()
        boxes = []

        for asset in assets:
            if not asset.createdAt:
                boxes.append(asset.id)

        return boxes

    async def spin_turntable(self) -> TurntableData:
        response = await self.send_request(
            request_type="GET", method="/tree/turntable/open"
        )
        return TurntableData(**response["result"])

    async def steal_claim(self, user_id: str) -> None:
        json_data = {
            "id": user_id,
        }

        await self.send_request(
            request_type="GET", method="/tree/steal/claim", params=json_data
        )

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


    async def claim_onchain(self, claim_data: dict):
        try:
            if claim_data.get("energy"):
                amount = claim_data["energy"]
            elif claim_data.get("amount"):
                amount = claim_data["amount"]
            else:
                raise Exception("Amount not provided")

            transaction = await self.build_forest_transaction(amount=amount, signature=claim_data["tx"])
            status, tx_hash = await self.send_and_verify_transaction(transaction)
            return status, tx_hash

        except Exception as error:
            raise Exception(f"Failed to claim points onchain: {error}")

    async def verify_wallet(self) -> ResponseData:
        json_data = {
            "jwtToken": self.jwt_token,
        }

        response = await self.send_request(method="/wallet/verify", json_data=json_data)
        return ResponseData(**response)


    async def get_points_forest_proof(self) -> dict:
        params = {
            "type": "Signin",
        }

        response = await self.send_request(
            request_type="GET",
            method="/tree/get-forest-proof",
            params=params,
        )

        return response["result"]


    async def get_referral_points_forest_proof(self) -> dict:
        params = {
            "type": "InviteClaim",
            "address": str(self.keypair.address),
        }

        response = await self.send_request(
            request_type="GET",
            method="/tree/get-forest-proof",
            params=params,
        )

        return response["result"]


    async def get_box_forest_proof(self, box_id: str) -> dict:
        params = {
            "type": "OpenReward",
            "boxId": box_id,
        }

        response = await self.send_request(
            request_type="GET",
            method="/tree/get-forest-proof",
            params=params,
        )

        return response["result"]


    async def get_turntable_forest_proof(self) -> dict:
        params = {
            'type': 'Turntable',
        }

        response = await self.send_request(
            request_type="GET",
            method="/tree/get-forest-proof",
            params=params,
        )

        return response["result"]


    async def get_steal_energy_forest_proof(self, user_id: str) -> dict:
        params = {
            'type': 'Steal',
            'id': user_id,
        }

        response = await self.send_request(
            request_type="GET",
            method="/tree/get-forest-proof",
            params=params,
        )

        return response["result"]


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
