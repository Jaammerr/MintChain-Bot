import re

from web3 import Web3, Account
from web3.exceptions import TransactionIndexingInProgress, TransactionNotFound, TimeExhausted

from models import BridgeData
from loguru import logger
from loader import config as cfg


class Bridge(Web3, Account):
    def __init__(self, amount: float, mnemonic_or_pk: str):
        super().__init__(Web3.HTTPProvider(cfg.sepolia_rpc_url))

        self.amount = amount
        self.nonce = None
        self.keypair = self.from_mnemonic(mnemonic_or_pk) if len(mnemonic_or_pk.split()) in (12, 24) else self.from_key(mnemonic_or_pk)
        self.contract = self.eth.contract(address=Web3.to_checksum_address(BridgeData.address), abi=BridgeData.abi)

    @property
    def address(self):
        return self.keypair.address

    def build_transaction(self):
        transaction = self.contract.functions.bridgeETHTo(
            self.address,
            200000,
            b"0x7375706572627269646765"
        )

        return transaction.build_transaction({
            "value": Web3.to_wei(self.amount, "ether"),
            "gasPrice": self.eth.gas_price,
            "nonce": self.eth.get_transaction_count(self.address) if not self.nonce else self.nonce,
            "gas": int(
                transaction.estimate_gas({"from": self.address}) * 1.2
            ),
        })

    def check_balance(self) -> None:
        balance = self.eth.get_balance(self.address)
        human_balance = self.from_wei(balance, "ether")

        if human_balance < self.amount:
            raise Exception(f"Insufficient balance: {human_balance} | Required: {self.amount} ETH")


    def send_transaction(self) -> bool:
        try:
            self.check_balance()

            signed_transaction = self.keypair.sign_transaction(self.build_transaction())
            transaction_hash = self.eth.send_raw_transaction(signed_transaction.rawTransaction)
            logger.debug(f"Account: {self.address} | Bridging {self.amount} ETH | Transaction hash: {transaction_hash.hex()}")
            status = self.eth.wait_for_transaction_receipt(transaction_hash, timeout=60)

            if status.status != 1:
                raise Exception(f"Failed to bridge {self.amount} ETH to MINT, transaction failed")

            logger.success(f"Account: {self.address} | Bridged {self.amount} ETH to MINT")

        except (TimeExhausted, TransactionNotFound, TransactionIndexingInProgress) as error:
            logger.error(f"Account: {self.address} | Transaction not found or time exhausted | {error} | Retrying...")
            return self.send_transaction()

        except Exception as error:
            if "nonce too low" in str(error):
                self.nonce = int(re.search(r"next nonce (\d+)", str(error)).group(1))
                logger.warning(f"Account: {self.address} | Nonce too low | Next nonce: {self.nonce} | Retrying...")
                return self.send_transaction()

            raise Exception(f"Failed to bridge {self.amount} ETH | {error}")
