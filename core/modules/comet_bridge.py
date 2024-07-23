import json

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

    @staticmethod
    def pad_to_32(x) -> str:
        return x.rjust(64, "0")

    async def build_bridge_transaction(self):
        function_signature = "0x78499054"
        destination_gas_cost = AsyncWeb3.to_wei(0.0003, "ether")
        amount = AsyncWeb3.to_wei(self.amount_to_bridge, "ether") + destination_gas_cost
        token_address = "0x0000000000000000000000000000000000000000".lower()
        provider_address = "0xb50ac92d6d8748ac42721c25a3e2c84637385a6b".lower()

        metadata = {"targetChain": "185", "targetAddress": self.to_address}

        encoded_metadata = (
            f"data:,{json.dumps(metadata, separators=(',', ':'))}".encode("utf-8").hex()
        )
        transaction_data = (
            function_signature
            + self.pad_to_32(hex(amount)[2:])
            + self.pad_to_32(token_address[2:])
            + self.pad_to_32(provider_address[2:].lower())
            + self.pad_to_32(
                hex(32 * 4)[2:]
            )  # Смещение для данных (4 параметра по 32 байта)
            + self.pad_to_32(
                hex(len(encoded_metadata) // 2)[2:]
            )  # Длина metadata в байтах
            + encoded_metadata
        )
        final_data = f"{transaction_data}0000000000000000"

        gas_limit = await self.eth.estimate_gas(
            {
                "chainId": 42161,
                "from": self.keypair.address,
                "to": AsyncWeb3.to_checksum_address(
                    "0x0fbCf4a62036E96C4F6770B38a9B536Aa14d1846"
                ),
                "value": amount,
                "data": final_data,
            }
        )

        return {
            "chainId": 42161,
            "from": self.keypair.address,
            "to": AsyncWeb3.to_checksum_address(
                "0x0fbCf4a62036E96C4F6770B38a9B536Aa14d1846"
            ),
            "value": amount,
            "gas": gas_limit,
            "gasPrice": await self.eth.gas_price,
            "nonce": await self.transactions_count(),
            "data": final_data,
        }
