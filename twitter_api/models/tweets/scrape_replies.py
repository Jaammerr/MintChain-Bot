from pydantic import BaseModel, field_validator
from twitter_api.errors import IncorrectData


class ScrapeTweetRepliesData(BaseModel):
    id: int | str
    limit: int = 200

    @field_validator("limit")
    @classmethod
    def limit_must_be_positive(cls, v):
        if v < 0:
            raise IncorrectData("Limit must be positive integer")

        return v


class UserData(BaseModel):
    id: int | str
    name: str
    screen_name: str
    profile_image_url: str
    favourites_count: int
    followers_count: int
    friends_count: int
    location: str
    description: str
    created_at: str


class ScrapeTweetRepliesResult(BaseModel):
    reply_text: str
    user_data: UserData


class ScrapeTweetRepliesResultData(BaseModel):
    replies: list[ScrapeTweetRepliesResult]
