from typing import Any

from pydantic import BaseModel, field_validator, validator, model_validator


class RankData(BaseModel):
    id: int
    address: str
    ens: Any
    amount: int
    role: str
    rank: int


class AssetData(BaseModel):
    id: int | None = None
    uid: int | None = None
    reward: Any | None = None
    type: str = "energy"
    openAt: Any | None = None
    createdAt: str | None = None


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
    ens: Any | None = None
    energy: int
    tree: int
    inviteId: int | None = None
    type: str = "normal"
    stake_id: int | None = None
    nft_id: int | None = None
    nft_pass: int | None = None
    signin: int
    code: Any | None = None
    createdAt: str
    invitePercent: int | None = None
    stealCount: int | None = None


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


class EnergyListData(BaseModel):
    class Energy(BaseModel):
        uid: list[str]
        amount: int
        includes: list[int]
        type: str
        id: str = None
        freeze: bool = None
        stealable: bool = None

        @model_validator(mode="before")
        @classmethod
        def validate_id(cls, values):
            if values["type"] != "daily":
                includes = [str(i) for i in values["includes"]]
                uid_str = "_".join(includes)
                values["id"] = f"{values['amount']}_{uid_str}"
            else:
                values["id"] = f"{values['amount']}_"

            return values

    result: list[Energy]


class TaskListData(BaseModel):
    class Task(BaseModel):
        id: int
        name: str
        amount: int
        isFreeze: bool
        spec: str
        claimed: bool | None = None

    result: list[Task]

