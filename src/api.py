import pyuseragents

from typing import Literal, List
from noble_tls import Session, Client
from twitter_api import Account as TwitterAccount
from twitter_api.models import BindAccountParamsV2

from models import *
from loader import config as configuration

from .wallet import Wallet
from .exceptions.base import APIError


class MintChainAPI(Wallet):
    API_URL = "https://www.mintchain.io/api"

    def __init__(self, account_data: Account):
        super().__init__(mnemonic=account_data.pk_or_mnemonic, rpc_url=configuration.rpc_url)
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

    async def get_tasks(self) -> dict:
        response = await self.send_request(
            request_type="GET", method=f"/tree/task-list?address={self.keypair.address}"
        )
        return response["result"]

    async def complete_task(self, task_id: int) -> int:
        response = await self.send_request(
            request_type="POST", method="/tree/task-submit", json_data={'id': task_id}
        )

        return response.get("result").get("amount")

    async def complete_all_tasks(self) -> None:
        tasks = await self.get_tasks()
        for task in tasks:
            if not task.get('claimed') and 'twitter' in task.get('spec'):
                reward = await self.complete_task(task.get('id'))
                logger.success(f"Account: {self.account.auth_token} | Earned: {reward} | Task {task['id']} done")

    async def is_daily_reward_claimed(self) -> bool:
        response = await self.send_request(
            request_type="GET", method="/tree/energy-list"
        )
        return response["result"][0]["freeze"]

    async def claim_daily_reward(self) -> int:
        json_data = {
            "uid": [],
            "amount": 500,
            "includes": [],
            "type": "daily",
            "freeze": False,
            "id": "500_",
        }

        response = await self.send_request(method="/tree/claim", json_data=json_data)
        return response["result"]

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

    async def inject(self, amount: int = None) -> InjectData:
        if not amount:
            amount = await self.energy_balance

        json_data = {
            "address": self.keypair.address,
            "energy": amount,
        }

        response = await self.send_request(method="/tree/inject", json_data=json_data)
        return InjectData(**response)

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

    async def update_proxy(self) -> bool:
        if self.account.proxy_change_url:
            response = await self.session.get(self.account.proxy_change_url)
            response.raise_for_status()

        return True
