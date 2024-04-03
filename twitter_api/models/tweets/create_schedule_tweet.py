from typing import List, Optional
from pydantic import BaseModel

from .create_tweet import MediaEntity


class CreateScheduleTweetData(BaseModel):
    text: str
    date: int | str
    media_entities: List[MediaEntity] | None = None


class CreateScheduleTweetResult(BaseModel):
    rest_id: str


class CreateScheduleTweetResultDataV1(BaseModel):
    tweet: Optional[CreateScheduleTweetResult]


class CreateScheduleTweetResultData(BaseModel):
    data: Optional[CreateScheduleTweetResultDataV1]
