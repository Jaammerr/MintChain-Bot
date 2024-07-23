import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Literal, Tuple, Any

import pyuseragents
from eth_account.messages import encode_typed_data, encode_defunct
from noble_tls import Client, Session
from pydantic import HttpUrl

from loader import config
from models import Account
from core.exceptions.base import APIError
from core.wallet import Wallet


class Vip3API(Wallet):
    API_URL = "https://dappapi.vip3.io/api"

    def __init__(self, account_data: Account):
        super().__init__(account_data.pk_or_mnemonic, config.mint_rpc_url)
        self.account = account_data
        self.session = self.setup_session()

    def setup_session(self) -> Session:
        session = Session(client=Client.CHROME_120)
        session.random_tls_extension_order = True

        session.timeout_seconds = 15
        session.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "content-type": "application/json",
            "origin": "https://dapp.vip3.io",
            "referer": "https://dapp.vip3.io/",
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
                if _response["code"] != 0:
                    raise APIError(f"{_response.get('msg')} | Method: {method}")

                return _response

            raise APIError(f"{_response} | Method: {method}")

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

    async def get_login_signature(self) -> tuple[str, Any]:
        message = f'Welcome to VIP3!\n\nClick "Sign" to sign in and accept the VIP3 Terms of Use(https://vip3.gitbook.io/term-of-use/).\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nWallet address:\n{self.keypair.address}\n\nNonce: {int(time.time() * 1000)}'

        encoded_message = encode_defunct(text=message)
        signed_message = self.keypair.sign_message(encoded_message)
        return message, signed_message.signature.hex()

    async def get_mint_data(self) -> dict:
        json_data = {
            "lang": "en",
            "chainId": 185,
        }

        response = await self.send_request(
            method="/v1/sbt/mint",
            json_data=json_data,
        )
        return response["data"]

    async def login(self) -> None:
        message, signature = await self.get_login_signature()

        json_data = {
            "address": self.keypair.address,
            "sign": signature,
            "raw": message,
        }

        response = await self.send_request(
            method="/v1/auth",
            json_data=json_data,
        )

        self.session.headers.update(
            {"Authorization": f"Bearer {response['data']['token']}"}
        )
