import asyncio
import re

from mailtmapi import MailTM
from mailtmapi.schemas.account import Account


class TempMail(MailTM):
    def __init__(self):
        super().__init__()
        self.account: Account | None = None

    async def generate_account(self, password: str = None):
        self.account = await self.get_account(password=password)

    async def get_verification_code(self):
        for _ in range(10):
            messages = await self.get_messages(self.account.token.token)
            for message in messages:
                if "subject" in str(message[1]):
                    message = message[1][0]
                    verification_code = re.search(r"\d{6}", message.intro)
                    if verification_code:
                        return verification_code.group()

            await asyncio.sleep(3)

        raise Exception("Failed to get verification code")
