from pydantic import BaseModel
from typing import Optional


class DeleteFavoriteTweetData(BaseModel):
    id: int | str


class DeleteFavoriteTweetResult(BaseModel):
    unfavorite_tweet: Optional[str]


class DeleteFavoriteTweetResultData(BaseModel):
    data: Optional[DeleteFavoriteTweetResult]
