from loguru import logger
from pydantic import BaseModel, field_validator


class Account(BaseModel):
    auth_token: str
    mnemonic: str
    proxy: str = None

    @field_validator("mnemonic", mode="before")
    def check_mnemonic(cls, value) -> str | None:
        words = value.split(" ")
        if len(words) not in (12, 24):
            logger.error(
                f"Mnemonic <<{value}>> is not in correct format | Need to be 12/24 words"
            )
            exit(1)

        return value

    @field_validator("proxy", mode="before")
    def check_proxy(cls, value) -> str | None:
        if not value:
            return None

        proxy_values = value.split(":")
        if len(proxy_values) != 4:
            logger.error(
                f"Proxy <<{value}>> is not in correct format | Need to be in format: <<ip:port:username:password>>"
            )
            exit(1)

        proxy_url = f"http://{proxy_values[2]}:{proxy_values[3]}@{proxy_values[0]}:{proxy_values[1]}"
        return proxy_url
