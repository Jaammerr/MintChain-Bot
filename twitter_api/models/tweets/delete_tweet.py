from pydantic import BaseModel


class DeleteTweetData(BaseModel):
    id: int | str


class DeleteTweetResult(BaseModel):
    pass


class DeleteTweetResultDataV2(BaseModel):
    tweet_results: DeleteTweetResult


class DeleteTweetResultDataV1(BaseModel):
    delete_tweet: DeleteTweetResultDataV2


class DeleteTweetResultData(BaseModel):
    data: DeleteTweetResultDataV1
