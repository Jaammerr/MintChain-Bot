from pydantic import BaseModel, field_validator
from twitter_api.errors import IncorrectData
from .scrape_favorites import UserData


class ScrapeTweetRetweetsData(BaseModel):
    id: int | str
    limit: int = 200

    @field_validator("limit")
    @classmethod
    def limit_must_be_positive(cls, v):
        if v < 0:
            raise IncorrectData("Limit must be positive integer")

        return v


class ScrapeTweetRetweetsResult(BaseModel):
    users: list[UserData]
