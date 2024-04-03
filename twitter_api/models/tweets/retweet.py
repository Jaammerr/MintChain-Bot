from typing import Optional

from pydantic import BaseModel


class CreateRetweetData(BaseModel):
    id: int | str


class Legacy(BaseModel):
    full_text: Optional[str]


class RetweetResult(BaseModel):
    rest_id: Optional[str]
    legacy: Optional[Legacy]


class RetweetResultDataV3(BaseModel):
    result: Optional[RetweetResult]


class RetweetResultDataV2(BaseModel):
    retweet_results: Optional[RetweetResultDataV3]


class RetweetResultDataV1(BaseModel):
    create_retweet: Optional[RetweetResultDataV2]


class RetweetResultData(BaseModel):
    data: Optional[RetweetResultDataV1]
