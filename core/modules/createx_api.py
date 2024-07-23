import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Literal

import pyuseragents
from eth_account.messages import encode_typed_data
from noble_tls import Client, Session

from loader import config
from models import Account
from core.exceptions.base import APIError
from core.wallet import Wallet


class CreateXAPI(Wallet):
    API_URL = "https://createx.art/api"

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
            "priority": "u=1, i",
            "referer": "https://createx.art/",
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
            if "status" in _response:
                if _response["status"] != 0:
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

    async def get_timestamp(self) -> tuple[int, str]:
        response = await self.send_request(
            request_type="GET",
            method="/v1/creator/public/timestamp",
        )

        timestamp = response["data"]["timestamp_ms"]
        timestamp_seconds = timestamp / 1000
        dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        formatted_date = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        return timestamp, formatted_date

    async def get_login_data(self) -> tuple[str, str]:
        timestamp, formatted_date = await self.get_timestamp()

        message = {
            "types": {
                "Message": [
                    {"name": "Message", "type": "string"},
                    {"name": "URI", "type": "string"},
                    {"name": "Version", "type": "string"},
                    {"name": "ChainId", "type": "uint256"},
                    {"name": "Nonce", "type": "uint256"},
                    {"name": "issuedAt", "type": "string"},
                ],
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
            },
            "primaryType": "Message",
            "domain": {"name": "", "version": "1", "chainId": "185"},
            "message": {
                "Message": "Sign in to the CreateX",
                "URI": "https://createx.art",
                "Version": "1",
                "ChainId": "185",
                "Nonce": timestamp,
                "issuedAt": formatted_date,
            },
        }
        signed_json = {
            "domain": {"name": "", "version": "1", "chainId": 185},
            "message": {
                "Message": "Sign in to the CreateX",
                "URI": "https://createx.art",
                "Version": "1",
                "ChainId": 185,
                "Nonce": timestamp,
                "issuedAt": formatted_date,
            },
            "primaryType": "Message",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "Message": [
                    {"name": "Message", "type": "string"},
                    {"name": "URI", "type": "string"},
                    {"name": "Version", "type": "string"},
                    {"name": "ChainId", "type": "uint256"},
                    {"name": "Nonce", "type": "uint256"},
                    {"name": "issuedAt", "type": "string"},
                ],
            },
        }

        encoded_message = encode_typed_data(full_message=message)
        signed_message = self.keypair.sign_message(encoded_message)
        return signed_message.signature.hex(), json.dumps(signed_json)

    async def create_collection(
        self, name: str, symbol: str, description: str, price: str, royalty_fee: str
    ) -> str:
        json_data = {
            "chain": "MINTCHAIN",
            "chain_name": "",
            "is_single_create": True,
            "nftUpload": True,
            "collection_name": name,
            "symbol": symbol,
            "description": description,
            "is_limit_count": False,
            "mint_price": price,
            "mint_start_time": int(time.time() * 1000),
            "mint_end_time": 0,
            "mint_qty_per_user": "1",
            "royalty_fee": royalty_fee,
            "royalty_fee_recipient": self.keypair.address,
            "collection_id": False,
            "is_image_update": False,
            "media_file_count": 1,
            "currency": "eth",
        }

        response = await self.send_request(
            request_type="POST",
            method="/v1/createx/create/collection",
            json_data=json_data,
        )
        return response["data"]["collection_id"]

    async def deploy(self, collection_id: str) -> str:
        json_data = {
            "chain": "MINTCHAIN",
            "chain_name": "MINTCHAIN",
            "collection_id": collection_id,
            "is_sbt": 0,
        }

        response = await self.send_request(
            request_type="POST",
            method="/v1/createx/create/direct_deploy",
            json_data=json_data,
        )

        return f"0x{response['data']['bin']}"

    async def create_query_collection(self, collection_id: str) -> dict:
        json_data = {
            "chain": "MINTCHAIN",
            "chain_name": "MINTCHAIN",
            "collection_id": collection_id,
        }

        response = await self.send_request(
            request_type="POST",
            method="/v1/createx/create/query_collection",
            json_data=json_data,
        )
        return response["data"]

    async def login(self) -> dict:
        signature, signed_json = await self.get_login_data()

        response = await self.send_request(
            method="/v1/creator/auth/login_with_type_data",
            json_data={
                "msg_signature": signature,
                "msg_signer": self.keypair.address,
                "signed_json": signed_json,
            },
        )

        return response
