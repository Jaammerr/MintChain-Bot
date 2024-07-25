import random
from typing import Any, Literal

from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import HttpUrl
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.eth import AsyncEth
from web3.types import Nonce

from models import (
    LoginData,
    CommemorativeNFTData,
    OmnihubData,
    MakeNFTGreatAgainData,
    SummerNFTData,
    MintFlagData,
    MintShopData,
    MintAir3Data,
    MintSupermintData,
    CometBridgeData,
    Vip3MintData,
    GreenIDData, GainfiMintData,
)

Account.enable_unaudited_hdwallet_features()


class Wallet(AsyncWeb3, Account):
    def __init__(self, mnemonic: str, rpc_url: HttpUrl | str):
        super().__init__(
            AsyncWeb3.AsyncHTTPProvider(str(rpc_url)),
            modules={"eth": (AsyncEth,)},
            middlewares=[],
        )
        self.keypair = (
            self.from_mnemonic(mnemonic)
            if len(mnemonic.split()) in (12, 24)
            else self.from_key(mnemonic)
        )

    @property
    def get_commemorative_nft_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(CommemorativeNFTData.address),
            abi=CommemorativeNFTData.abi,
        )


    @property
    def get_gainfi_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(GainfiMintData.address),
            abi=GainfiMintData.abi,
        )

    @property
    def get_omnihub_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(OmnihubData.address),
            abi=OmnihubData.abi,
        )

    @property
    def get_make_nft_great_again_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(MakeNFTGreatAgainData.address),
            abi=MakeNFTGreatAgainData.abi,
        )

    @property
    def get_summer_nft_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(SummerNFTData.address),
            abi=SummerNFTData.abi,
        )

    @property
    def get_mint_flag_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(MintFlagData.address),
            abi=MintFlagData.abi,
        )

    @property
    def get_min_shop_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(MintShopData.address),
            abi=MintShopData.abi,
        )

    @property
    def get_mint_air3_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(MintAir3Data.address),
            abi=MintAir3Data.abi,
        )

    @property
    def get_mint_supermint_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(MintSupermintData.address),
            abi=MintSupermintData.abi,
        )

    @property
    def get_comet_bridge_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(CometBridgeData.address),
            abi=CometBridgeData.abi,
        )

    @property
    def get_vip3_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(Vip3MintData.address),
            abi=Vip3MintData.abi,
        )

    @property
    def get_green_contract(self) -> AsyncContract:
        return self.eth.contract(
            address=AsyncWeb3.to_checksum_address(GreenIDData.address),
            abi=GreenIDData.abi,
        )

    async def transactions_count(self) -> Nonce:
        return await self.eth.get_transaction_count(self.keypair.address)

    async def check_balance(self) -> None:
        balance = await self.eth.get_balance(self.keypair.address)

        if balance <= 0:
            raise Exception(f"ETH balance is empty")

    async def human_balance(self) -> float | int:
        balance = await self.eth.get_balance(self.keypair.address)
        return AsyncWeb3.from_wei(balance, "ether")

    async def build_make_nft_great_again_transaction(self, proofs: list[str]):
        contract = self.get_make_nft_great_again_contract
        transaction = contract.functions.awardItem(proofs)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_green_id_nft_transaction(self, mint_id: int):
        contract = self.get_green_contract
        transaction = contract.functions.claim(mint_id)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_mint_air3_transaction(self):
        contract = self.get_mint_air3_contract
        transaction = contract.functions.mint(1)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_mint_supermint_transaction(self):
        contract = self.get_mint_supermint_contract
        transaction = contract.functions.mint(1)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_mint_shop_transaction(self):
        contract = self.get_min_shop_contract
        transaction = contract.functions.mint(1)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_mint_flag_transaction(self):
        contract = self.get_mint_flag_contract
        transaction = contract.functions.mint(1)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_gainfi_mint_transaction(self, mint_data: dict):
        contract = self.get_gainfi_contract
        transaction = contract.functions.pumpMasterMint(
            self.keypair.address,
            mint_data["id"],
            mint_data["sign"],
        )

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_summer_nft_transaction(self):
        contract = self.get_summer_nft_contract
        transaction = contract.functions.claim(
            self.keypair.address,
            1,
            AsyncWeb3.to_checksum_address("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"),
            0,
            (
                ["0x0000000000000000000000000000000000000000000000000000000000000000"],
                115792089237316195423570985008687907853269984665640564039457584007913129639935,
                0,
                AsyncWeb3.to_checksum_address(
                    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                ),
            ),
            b"",
        )

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_vip3_nft_transaction(self, mint_data: dict):
        contract = self.get_vip3_contract
        transaction = contract.functions.mint(
            self.keypair.address,
            mint_data["data"]["deadline"],
            mint_data["data"]["level"],
            0,
            mint_data["data"]["signature"],
        )

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_commemorative_nft_transaction(self):
        contract = self.get_commemorative_nft_contract
        transaction = contract.functions.mint(1)

        return await transaction.build_transaction(
            {
                "gasPrice": await self.eth.gas_price,
                "nonce": await self.transactions_count(),
                "gas": int(
                    await transaction.estimate_gas({"from": self.keypair.address}) * 1.2
                ),
            }
        )

    async def build_createx_collection_transaction(self, data: str):
        transaction = {
            "from": self.keypair.address,
            "data": data,
            "nonce": await self.transactions_count(),
        }

        estimated_gas = await self.eth.estimate_gas(transaction)
        transaction["gas"] = int(estimated_gas * 1.2)
        transaction["gasPrice"] = await self.eth.gas_price

        return transaction

    async def build_owlto_summer_fest_nft_transaction(self):
        transaction = {
            "from": self.keypair.address,
            "to": AsyncWeb3.to_checksum_address(
                "0x0000C019d60b628F9Ba553092CdA375191319c5e"
            ),
            "value": AsyncWeb3.to_wei(0.0001, "ether"),
            "data": "0x5e752eb40000000000000000000000000c1308dd0b5886b48cb14da2d6cf766cfc8be6ea0000000000000000000000000000000000000000000000000000000000000001",
            "nonce": await self.transactions_count(),
        }

        estimated_gas = await self.eth.estimate_gas(transaction)
        transaction["gas"] = int(estimated_gas * 1.2)
        transaction["gasPrice"] = await self.eth.gas_price

        return transaction

    async def build_omnihub_summer_fest_nft_transaction(self):
        transaction = {
            "from": self.keypair.address,
            "to": AsyncWeb3.to_checksum_address(
                "0x0000C019d60b628F9Ba553092CdA375191319c5e"
            ),
            "value": AsyncWeb3.to_wei(0.0001, "ether"),
            "data": "0x5e752eb400000000000000000000000050b42f700a5feba13ee6437c43fac4df33062f2b0000000000000000000000000000000000000000000000000000000000000001",
            "nonce": await self.transactions_count(),
        }

        estimated_gas = await self.eth.estimate_gas(transaction)
        transaction["gas"] = int(estimated_gas * 1.2)
        transaction["gasPrice"] = await self.eth.gas_price

        return transaction

    @property
    def get_forest_message(self) -> str:
        message = f"You are participating in the Mint Forest event: \n {self.keypair.address}\n\nNonce: {str(random.randint(1000000, 9000000))}"
        return message

    @property
    def get_airdrop_message(self) -> str:
        message = f"You are participating in the Mint Airdrop event: \n {self.keypair.address}\n\nNonce: {str(random.randint(1000000, 9000000))}"
        return message

    def sign_mint_message(self, type_: Literal["airdrop", "forest"]) -> LoginData:
        if type_ == "forest":
            message = self.get_forest_message
        else:
            message = self.get_airdrop_message
        encoded_message = encode_defunct(text=message)
        signed_message = self.keypair.sign_message(encoded_message)
        return LoginData(message=message, signed_message=signed_message.signature.hex())

    async def send_and_verify_transaction(self, trx: Any) -> tuple[bool | Any, str]:
        signed = self.keypair.sign_transaction(trx)
        tx_hash = await self.eth.send_raw_transaction(signed.rawTransaction)
        receipt = await self.eth.wait_for_transaction_receipt(tx_hash)
        return receipt["status"] == 1, tx_hash.hex()
