from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr

    # model_config = ConfigDict(from_attributes=True)


class UserCreate(User):
    password: str


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
