from pydantic import BaseModel
from typing import Optional


class DeleteRetweetData(BaseModel):
    id: int | str


class Legacy(BaseModel):
    full_text: Optional[str]


class DeleteRetweetResult(BaseModel):
    rest_id: Optional[str]
    legacy: Optional[Legacy]


class DeleteRetweetResultDataV3(BaseModel):
    result: Optional[DeleteRetweetResult]


class DeleteRetweetResultDataV2(BaseModel):
    source_tweet_results: Optional[DeleteRetweetResultDataV3]


class DeleteRetweetResultDataV1(BaseModel):
    unretweet: Optional[DeleteRetweetResultDataV2]


class DeleteRetweetResultData(BaseModel):
    data: Optional[DeleteRetweetResultDataV1]
