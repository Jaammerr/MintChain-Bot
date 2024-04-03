from typing import Optional

from pydantic import BaseModel


class DeleteScheduleTweetData(BaseModel):
    id: str | int


class DeleteScheduleTweetResult(BaseModel):
    scheduledtweet_delete: Optional[str]


class DeleteScheduleTweetResultData(BaseModel):
    data: Optional[DeleteScheduleTweetResult]
