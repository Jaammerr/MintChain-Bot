from pydantic import BaseModel, field_validator, HttpUrl


class BindAccountParamsV1(BaseModel):
    url: HttpUrl


class BindAccountDataV1(BaseModel):
    url: HttpUrl
    oauth_token: str
    oauth_verifier: str
