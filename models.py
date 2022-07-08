from pydantic import BaseModel


class UserCreationModel(BaseModel):
    username: str
    email: str
    password: str


class UserUpdateModel(BaseModel):
    email: str | None
    password: str | None


class User(BaseModel):
    id: int
    username: str
    email: str


class UserAuth(BaseModel):
    username: str
    password_hash: str


class TokenData(BaseModel):
    username: str | None = None
