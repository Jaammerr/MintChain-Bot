from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from twitter_api.errors import IncorrectData


class UserFollowersData(BaseModel):
    username: str
    limit: int = 200

    @field_validator("limit")
    @classmethod
    def limit_must_be_positive(cls, v):
        if v < 0:
            raise IncorrectData("Limit must be positive integer")

        return v
