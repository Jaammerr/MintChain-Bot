from pydantic import BaseModel
from typing import Optional


class CreateFavoriteTweetData(BaseModel):
    id: int | str


class FavoriteTweetResult(BaseModel):
    favorite_tweet: Optional[str]


class FavoriteTweetResultData(BaseModel):
    data: Optional[FavoriteTweetResult]
