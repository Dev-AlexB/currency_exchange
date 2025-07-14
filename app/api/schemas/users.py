from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@$!%*?&])[A-Za-z\d@$!%*?&]+$"


def normalize(value: str) -> str:
    return value.lower()


class UserBase(BaseModel):
    username: Annotated[str, BeforeValidator(normalize)]
    email: Annotated[EmailStr, BeforeValidator(normalize)]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: Annotated[
        str, Field(min_length=8, max_length=50, pattern=pattern)
    ]


class UserReturn(UserBase):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
