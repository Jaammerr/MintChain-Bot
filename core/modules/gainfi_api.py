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


class GainfiAPI(Wallet):
    API_URL = "https://devapi.gainfi.xyz"

    def __init__(self, account_data: Account):
        super().__init__(account_data.pk_or_mnemonic, config.mint_rpc_url)
        self.account = account_data
        self.session = self.setup_session()

    def setup_session(self) -> Session:
        session = Session(client=Client.CHROME_120)
        session.random_tls_extension_order = True

        session.timeout_seconds = 15
        session.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
            'chain': '185',
            'content-type': 'application/json',
            'language': 'en',
            'origin': 'https://dev.gainfi.xyz',
            'priority': 'u=1, i',
            'referer': 'https://dev.gainfi.xyz/',
            'user-agent': pyuseragents.random(),
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
                if _response["code"] != 200:
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


    async def send_email_code(self, email: str) -> dict:
        json_data = {
            'email': email,
            'walletAddress': str(self.keypair.address),
        }

        return await self.send_request(
            request_type="POST",
            method="/website/sendEmail",
            json_data=json_data,
        )


    async def verify_email(self, email: str, code: str) -> dict:
        json_data = {
            'email': email,
            'code': code,
            'walletAddress': str(self.keypair.address),
        }

        return (await self.send_request(
            request_type="POST",
            method="/website/validEmailByCode",
            json_data=json_data,
        ))['data']

    async def login(self) -> None:

        json_data = {
            'walletAddress': str(self.keypair.address),
        }

        response = await self.send_request(
            request_type="POST",
            method="/login/loginIn",
            json_data=json_data,
        )

        self.session.headers.update(
            {"Authorization": f"Bearer {response['data']['token']}"}
        )
