from typing import Annotated, Protocol

from fastapi import Depends

from app.api.db.models import User
from app.api.db.UoW import IUserUnitOfWork, UserUnitOfWork
from app.api.errors.exceptions import (
    UniqueFieldException,
    UserUnauthorisedException,
)
from app.api.schemas.users import UserCreate, UserReturn
from app.core.security import verify_password


class IUserService(Protocol):
    async def register_user(self, user: UserCreate) -> UserReturn: ...
    async def authenticate_user(self, username: str, password: str) -> str: ...


class UserService:
    def __init__(self, uow: IUserUnitOfWork) -> None:
        self.uow = uow

    async def register_user(self, user: UserCreate) -> UserReturn:
        async with self.uow:
            if await self.uow.user_repo.get_by_username(user.username):
                raise UniqueFieldException("username", user.username)
            if await self.uow.user_repo.get_by_email(user.email):
                raise UniqueFieldException("email", user.email)
            model = await self.uow.user_repo.add_one(User.from_schema(user))
            return UserReturn.model_validate(model)

    async def authenticate_user(self, username: str, password: str) -> str:
        async with self.uow:
            user: User = await self.uow.user_repo.get_by_username(
                username.lower()
            )
        if user and verify_password(password, user.hashed_password):
            return user.username
        raise UserUnauthorisedException()


async def get_user_service(
    uow: Annotated[IUserUnitOfWork, Depends(UserUnitOfWork)]
) -> IUserService:
    return UserService(uow)
