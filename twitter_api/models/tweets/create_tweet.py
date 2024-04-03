from typing import List, Optional, Any, Dict

from pydantic import BaseModel, field_validator
from twitter_api.errors import IncorrectData


class MediaEntity(BaseModel):
    media_id: int
    tagged_users: List[str] | None = []

    @field_validator("tagged_users")
    @classmethod
    def validate_users(cls, users: List[str]):
        if users:
            if len(users) > 10:
                raise IncorrectData("Maximum 10 tagged users allowed")

        return users


class CreateTweetData(BaseModel):
    text: str
    media_entities: List[MediaEntity] | None = None


class Legacy(BaseModel):
    can_dm: Optional[bool]
    can_media_tag: Optional[bool]
    created_at: Optional[str]
    default_profile: Optional[bool]
    default_profile_image: Optional[bool]
    description: Optional[str]
    entities: Optional[Dict[str, Any]]
    fast_followers_count: Optional[int]
    favourites_count: Optional[int]
    followers_count: Optional[int]
    friends_count: Optional[int]
    has_custom_timelines: Optional[bool]
    is_translator: Optional[bool]
    listed_count: Optional[int]
    location: Optional[str]
    media_count: Optional[int]
    name: Optional[str]
    needs_phone_verification: Optional[bool]
    normal_followers_count: Optional[int]
    pinned_tweet_ids_str: Optional[List[str]]
    possibly_sensitive: Optional[bool]
    profile_image_url_https: Optional[str]
    profile_interstitial_type: Optional[str]
    screen_name: Optional[str]
    statuses_count: Optional[int]
    translator_type: Optional[str]
    verified: Optional[bool]
    want_retweets: Optional[bool]
    withheld_in_countries: Optional[List[str]]


class UserResult(BaseModel):
    __typename: Optional[str]
    id: Optional[str]
    rest_id: Optional[str]
    affiliates_highlighted_label: Optional[Dict[str, Any]]
    has_graduated_access: Optional[bool]
    is_blue_verified: Optional[bool]
    profile_image_shape: Optional[str]
    legacy: Optional[Legacy]
    smart_blocked_by: Optional[bool]
    smart_blocking: Optional[bool]


class Result(BaseModel):
    result: Optional[UserResult]


class Core(BaseModel):
    user_results: Optional[Result]


class Views(BaseModel):
    state: Optional[str]


class Entities(BaseModel):
    user_mentions: Optional[List[Any]]
    urls: Optional[List[Any]]
    hashtags: Optional[List[Any]]
    symbols: Optional[List[Any]]


class Legacy2(BaseModel):
    bookmark_count: Optional[int]
    bookmarked: Optional[bool]
    created_at: Optional[str]
    conversation_id_str: Optional[str]
    display_text_range: Optional[List[int]]
    entities: Optional[Entities]
    favorite_count: Optional[int]
    favorited: Optional[bool]
    full_text: Optional[str]
    is_quote_status: Optional[bool]
    lang: Optional[str]
    quote_count: Optional[int]
    reply_count: Optional[int]
    retweet_count: Optional[int]
    retweeted: Optional[bool]
    user_id_str: Optional[str]
    id_str: Optional[str]


class EditControl(BaseModel):
    edit_tweet_ids: Optional[List[str]]
    editable_until_msecs: Optional[str]
    is_edit_eligible: Optional[bool]
    edits_remaining: Optional[str]


class QuickPromoteEligibility(BaseModel):
    eligibility: Optional[str]


class UnmentionData(BaseModel):
    pass


class UnmentionInfo(BaseModel):
    pass


class CreateTweetResult(BaseModel):
    rest_id: Optional[str]
    has_birdwatch_notes: Optional[bool]
    core: Optional[Core]
    unmention_data: Optional[UnmentionData]
    edit_control: Optional[EditControl]
    is_translatable: Optional[bool]
    views: Optional[Views]
    source: Optional[str]
    legacy: Optional[Legacy2]
    quick_promote_eligibility: Optional[QuickPromoteEligibility]
    unmention_info: Optional[UnmentionInfo]


class CreateTweetResultDataV3(BaseModel):
    result: Optional[CreateTweetResult]


class CreateTweetResultDataV2(BaseModel):
    tweet_results: Optional[CreateTweetResultDataV3]


class CreateTweetResultDataV1(BaseModel):
    create_tweet: Optional[CreateTweetResultDataV2]


class CreateTweetResultData(BaseModel):
    data: Optional[CreateTweetResultDataV1]
