from pydantic import BaseModel, field_validator, HttpUrl


class BindAccountParamsV2(BaseModel):
    code_challenge: str
    code_challenge_method: str = "plain"
    client_id: str
    redirect_uri: HttpUrl
    response_type: str = "code"
    scope: str = "tweet.read users.read follows.read offline.access"
    state: str

    @field_validator("redirect_uri", mode="after")
    def validate_uri(cls, value):
        # url = HttpUrl("https://google.com")
        return str(value)


class BindAccountDataV2(BaseModel):
    code: str
