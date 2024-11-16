import json

from eth_utils import to_hex
from pydantic import HttpUrl
from web3 import AsyncWeb3

from core.wallet import Wallet


class CometBridge(Wallet):
    def __init__(
        self,
        amount_to_bridge: float,
        to_address: str,
        mnemonic: str,
        rpc_url: HttpUrl | str,
    ):
        super().__init__(mnemonic, rpc_url)
        self.amount_to_bridge = amount_to_bridge
        self.to_address = to_address


    async def build_bridge_transaction(self):
        metadata = {
            "targetChain": "185",
            "targetAddress": self.to_address,
        }
        metadata = f'data:,{json.dumps(metadata, separators=(",", ":"))}'
        final_data = to_hex(text=metadata)
        value = self.to_wei(0.0004, "ether") + self.to_wei(self.amount_to_bridge, "ether")

        gas_limit = await self.eth.estimate_gas(
            {
                "chainId": 10,
                "from": self.keypair.address,
                "to": AsyncWeb3.to_checksum_address(
                    "0xb50ac92d6d8748ac42721c25a3e2c84637385a6b"
                ),
                "value": value,
                "data": final_data,
            }
        )

        return {
            "chainId": 10,
            "from": self.keypair.address,
            "to": AsyncWeb3.to_checksum_address(
                "0xb50ac92d6d8748ac42721c25a3e2c84637385a6b"
            ),
            "value": value,
            "gas": gas_limit,
            "gasPrice": await self.eth.gas_price,
            "nonce": await self.transactions_count(),
            "data": final_data,
        }
