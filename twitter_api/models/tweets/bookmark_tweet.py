from pydantic import BaseModel
from typing import Optional, Dict


class CreateBookmarkData(BaseModel):
    id: str | int


class CreateBookmarkResult(BaseModel):
    tweet_bookmark_put: Optional[str]


class CreateBookmarkResultData(BaseModel):
    data: Optional[CreateBookmarkResult]
