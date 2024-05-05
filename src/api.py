import asyncio
import random
import pyuseragents

from typing import Literal, List
from noble_tls import Session, Client

from models import EnergyListData
from twitter_api import Account as TwitterAccount
from twitter_api.models import BindAccountParamsV2

from models import *
from loader import config as configuration

from .wallet import Wallet
from .exceptions.base import APIError
from .bridge import Bridge


class MintChainAPI(Wallet):
    API_URL = "https://www.mintchain.io/api"

    def __init__(self, account_data: Account):
        super().__init__(mnemonic=account_data.pk_or_mnemonic, rpc_url=configuration.eth_rpc_url)
        self.account = account_data
        self.session = self.setup_session()

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
            "authority": "www.mintchain.io",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "authorization": "Bearer",
            "content-type": "application/json",
            "origin": "https://www.mintchain.io",
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
    ):
        def _verify_response(_response: dict) -> dict:
            if "code" in _response:
                if _response["code"] != 10000:
                    raise APIError(f"{_response.get('msg')} | Method: {method}")

                return _response

            raise APIError(f"{_response} | Method: {method}")

        if request_type == "POST":
            if not url:
                response = await self.session.post(
                    f"{self.API_URL}{method}", json=json_data, params=params
                )

            else:
                response = await self.session.post(url, json=json_data, params=params)

        else:
            if not url:
                response = await self.session.get(
                    f"{self.API_URL}{method}", params=params
                )

            else:
                response = await self.session.get(url, params=params)

        response.raise_for_status()
        return _verify_response(response.json())

    async def is_daily_reward_claimed(self) -> bool:
        response = await self.send_request(
            request_type="GET", method="/tree/energy-list"
        )
        return response["result"][-1]["freeze"]


    async def get_energy_list(self) -> EnergyListData:
        response = await self.send_request(request_type="GET", method="/tree/energy-list")
        return EnergyListData(**response)

    async def get_task_list(self) -> TaskListData:
        response = await self.send_request(request_type="GET", method=f"/tree/task-list?address={self.keypair.address}")
        return TaskListData(**response)

    async def complete_tasks(self):
        task_list = await self.get_task_list()
        for task in task_list.result:
            if task.spec not in ("discord-follow", "stake"):
                if task.claimed:
                    logger.debug(f"Account: {self.account.auth_token} | Task already completed: {task.name}")
                    continue

                try:
                    await self.submit_task_id(task.id)
                    logger.debug(f"Account: {self.account.auth_token} | Task completed: {task.name} | Reward: {task.amount} energy")
                    await asyncio.sleep(1)

                except APIError as error:
                    logger.error(f"Account: {self.account.auth_token} | Failed to complete task: {task.name} | {error}")
                    await asyncio.sleep(1)

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
                    logger.debug(f"Account: {self.account.auth_token} | Daily reward already claimed")
                    continue
                else:
                    json_data["freeze"] = energy.freeze

            await self.send_request(method="/tree/claim", json_data=json_data)
            logger.debug(f"Account: {self.account.auth_token} | Claimed {energy.amount} energy | Type: {energy.type}")
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

        twitter_account = TwitterAccount.run(
            auth_token=self.account.auth_token,
            setup_session=True,
            proxy=self.account.proxy,
        )
        bind_data = twitter_account.bind_account_v2(
            bind_params=BindAccountParamsV2(**params)
        )

        params = {
            "code": bind_data.code,
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

    async def user_info(self) -> UserInfo:
        response = await self.send_request(request_type="GET", method="/tree/user-info")
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

    async def claim_boxes(self):
        assets = await self.assets()
        for asset in assets:
            if not asset.createdAt:
                try:
                    opened_box_data = await self.open_box(asset.id)
                    logger.debug(f"Account: {self.account.auth_token} | Box opened | Reward: {opened_box_data.energy} energy")
                except APIError as error:
                    logger.error(f"Account: {self.account.auth_token} | Failed to open box: {asset.type} | {error}")

                await asyncio.sleep(1)

    async def spin_turntable(self) -> TurntableData:
        response = await self.send_request(request_type="GET", method="/tree/turntable/open")
        return TurntableData(**response["result"])

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


    async def submit_task_id(self, task_id: int) -> None:
        json_data = {
            'id': task_id,
        }

        await self.send_request(method="/tree/task-submit", json_data=json_data)

    async def testnet_bridge(self) -> None:
        amount_to_bridge = random.uniform(configuration.min_amount_to_bridge, configuration.max_amount_to_bridge)
        bridge = Bridge(amount=amount_to_bridge, mnemonic_or_pk=self.account.pk_or_mnemonic)
        bridge.send_transaction()

    async def verify_wallet(self) -> ResponseData:
        json_data = {
            "jwtToken": self.jwt_token,
        }

        response = await self.send_request(method="/wallet/verify", json_data=json_data)
        return ResponseData(**response)

    async def login(self):
        messages = self.sign_login_message()
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
