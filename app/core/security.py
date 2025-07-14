import datetime
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.api.errors.exceptions import InvalidTokenException
from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes="bcrypt")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=settings.JWT.EXPIRES_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM
    )


def get_username_from_token(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> str:
    try:
        payload = jwt.decode(
            token, settings.JWT.SECRET_KEY, algorithms=[settings.JWT.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.ExpiredSignatureError as e:
        raise InvalidTokenException(detail="Токен устарел") from e
    except jwt.InvalidTokenError as e:
        raise InvalidTokenException(detail="Ошибка чтения токена") from e
