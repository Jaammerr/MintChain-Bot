from typing import Any

from pydantic import BaseModel


class RankData(BaseModel):
    id: int
    address: str
    ens: Any
    amount: int
    role: str
    rank: int


class AssetData(BaseModel):
    id: int
    uid: int
    reward: Any
    type: str = "energy"
    openAt: Any
    createdAt: str


class OpenBoxData(BaseModel):
    energy: int
    type: str = "energy"


class ClaimData(BaseModel):
    code: int
    result: int
    msg: str


class InjectData(BaseModel):
    code: int
    result: bool
    msg: str


class UserInfo(BaseModel):
    id: int
    treeId: int
    address: str
    ens: Any
    energy: int
    tree: int
    inviteId: int
    type: str = "normal"
    stake_id: int
    nft_id: int
    nft_pass: int
    signin: int
    code: Any
    createdAt: str
    invitePercent: int


class ResponseData(BaseModel):
    code: int
    result: Any | None = None
    msg: str


class LoginWalletData(BaseModel):
    class User(BaseModel):
        id: int
        address: str
        status: str
        inviteId: None | int
        twitter: None | str
        discord: None | str

    access_token: str
    user: User
