from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from web3.types import Nonce

from models import LoginData


Account.enable_unaudited_hdwallet_features()


class Wallet(Web3, Account):
    def __init__(self, mnemonic: str, rpc_url: str):
        super().__init__(Web3.HTTPProvider(rpc_url))
        self.keypair = self.from_mnemonic(mnemonic) if len(mnemonic.split()) in (12, 24) else self.from_key(mnemonic)

    @property
    def transactions_count(self) -> Nonce:
        return self.eth.get_transaction_count(self.keypair.address)

    @property
    def get_message(self) -> str:
        message = f"You are participating in the Mint Forest event: \n {self.keypair.address}\n\nNonce: {self.transactions_count}"
        return message

    def sign_login_message(self) -> LoginData:
        encoded_message = encode_defunct(text=self.get_message)
        signed_message = self.keypair.sign_message(encoded_message)
        return LoginData(
            message=self.get_message, signed_message=signed_message.signature.hex()
        )
