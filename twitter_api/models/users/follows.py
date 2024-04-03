from typing import Optional, List

from pydantic import BaseModel, model_validator
from twitter_api.errors import IncorrectData


class UnfollowUserData(BaseModel):
    id: int | str = None
    username: str = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: dict):
        if not values.get("id") and not values.get("username"):
            raise IncorrectData("Either id or username must be provided")

        return values


class FollowUserData(BaseModel):
    id: str | int = None
    username: str = None

    @model_validator(mode="before")
    @classmethod
    def validate_data(cls, values: dict):
        if not values.get("id") and not values.get("username"):
            raise IncorrectData("Either id or username must be provided")

        return values


class FollowsUserResult(BaseModel):
    id: Optional[int]
    id_str: Optional[str]
    name: Optional[str]
    screen_name: Optional[str]
    location: Optional[str]
    description: Optional[str]
    url: Optional[str]
    protected: Optional[bool]
    followers_count: Optional[int]
    fast_followers_count: Optional[int]
    normal_followers_count: Optional[int]
    friends_count: Optional[int]
    listed_count: Optional[int]
    created_at: Optional[str]
    favourites_count: Optional[int]
    utc_offset: Optional[int]
    time_zone: Optional[str]
    geo_enabled: Optional[bool]
    verified: Optional[bool]
    statuses_count: Optional[int]
    media_count: Optional[int]
    lang: Optional[str]
    profile_image_url: Optional[str]
    profile_image_url_https: Optional[str]
    profile_banner_url: Optional[str]
    pinned_tweet_ids: Optional[List[int]]
    pinned_tweet_ids_str: Optional[List[str]]
    has_custom_timelines: Optional[bool]
    can_dm: Optional[bool]
    can_media_tag: Optional[bool]
    following: Optional[bool]
    follow_request_sent: Optional[bool]
    blocking: Optional[bool]
    business_profile_state: Optional[str]
    followed_by: Optional[bool]
    ext_is_blue_verified: Optional[bool]
    ext_has_nft_avatar: Optional[bool]
