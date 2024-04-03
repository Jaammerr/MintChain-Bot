from pydantic import BaseModel
from typing import Optional, Dict, List, Any

from .create_tweet import MediaEntity


class CreateReplyData(BaseModel):
    id: str | int
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


class UserResults(BaseModel):
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


class CoreUserResult(BaseModel):
    result: Optional[UserResults]


class Core(BaseModel):
    user_results: Optional[CoreUserResult]


class Views(BaseModel):
    state: Optional[str]


class EditControl(BaseModel):
    edit_tweet_ids: Optional[List[str]]
    editable_until_msecs: Optional[str]
    is_edit_eligible: Optional[bool]
    edits_remaining: Optional[str]


class Media(BaseModel):
    display_url: Optional[str]
    expanded_url: Optional[str]
    id_str: Optional[str]
    indices: Optional[List[int]]
    media_url_https: Optional[str]
    type: Optional[str]
    url: Optional[str]
    features: Optional[Dict[str, Any]]
    sizes: Optional[Dict[str, Any]]
    original_info: Optional[Dict[str, int]]


class Entities(BaseModel):
    user_mentions: Optional[List[Dict[str, Any]]]
    urls: Optional[List[Any]]
    hashtags: Optional[List[Any]]
    symbols: Optional[List[Any]]


class ExtendedEntities(BaseModel):
    media: Optional[List[Media]]


class Legacy2(BaseModel):
    bookmark_count: Optional[int]
    bookmarked: Optional[bool]
    created_at: Optional[str]
    conversation_id_str: Optional[str]
    entities: Optional[Entities]
    favorite_count: Optional[int]
    favorited: Optional[bool]
    full_text: Optional[str]
    in_reply_to_screen_name: Optional[str]
    in_reply_to_status_id_str: Optional[str]
    in_reply_to_user_id_str: Optional[str]
    is_quote_status: Optional[bool]
    lang: Optional[str]
    quote_count: Optional[int]
    reply_count: Optional[int]
    retweet_count: Optional[int]
    retweeted: Optional[bool]
    user_id_str: Optional[str]
    id_str: Optional[str]


class UnmentionInfo(BaseModel):
    pass


class CreateReplyResult(BaseModel):
    rest_id: Optional[str]
    has_birdwatch_notes: Optional[bool]
    core: Optional[Core]
    is_translatable: Optional[bool]
    views: Optional[Views]
    source: Optional[str]
    legacy: Optional[Legacy2]


class CreateReplyResultDataV3(BaseModel):
    result: Optional[CreateReplyResult]


class CreateReplyResultDataV2(BaseModel):
    tweet_results: Optional[CreateReplyResultDataV3]


class CreateReplyResultDataV1(BaseModel):
    create_tweet: Optional[CreateReplyResultDataV2]


class CreateReplyResultData(BaseModel):
    data: Optional[CreateReplyResultDataV1]
