from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


def validate_password(value: str) -> str:
    allowed_specials = "!@$%*?&"
    if not any(c.isupper() for c in value):
        raise ValueError("Пароль должен содержать заглавную букву")
    if not any(c.islower() for c in value):
        raise ValueError("Пароль должен содержать строчную букву")
    if not any(c.isdigit() for c in value):
        raise ValueError("Пароль должен содержать цифру")
    if not any(c in allowed_specials for c in value):
        raise ValueError(
            f"Пароль должен содержать символ из набора {allowed_specials}"
        )
    if not all(c.isalnum() or c in allowed_specials for c in value):
        raise ValueError("Пароль не должен содержать недопустимые символы")
    return value


def normalize(value: str) -> str:
    return value.lower()


class UserBase(BaseModel):
    username: Annotated[str, AfterValidator(normalize)]
    email: Annotated[EmailStr, AfterValidator(normalize)]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: Annotated[
        str,
        Field(min_length=8, max_length=50),
        AfterValidator(validate_password),
    ]


class UserReturn(UserBase):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
