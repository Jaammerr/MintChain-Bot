from pydantic import BaseModel
from typing import Optional, Dict


class DeleteBookmarkData(BaseModel):
    id: str | int


class DeleteBookmarkResult(BaseModel):
    tweet_bookmark_delete: Optional[str]


class DeleteBookmarkResultData(BaseModel):
    data: Optional[DeleteBookmarkResult]
