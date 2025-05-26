from typing import Annotated

from fastapi import Depends

from app.api.db.database import AbstractUserRepository, get_user_repo
from app.api.schemas.users import User, UserCreate, UserInDB
from app.core.security import authenticate_user as au


class UserService:
    def __init__(self, repo: AbstractUserRepository):
        self.repo = repo

    def register_user(self, user: UserCreate) -> User:
        return self.repo.add_user(user)

    def read_user_from_db(self, username: str) -> UserInDB:
        return self.repo.get_user(username)

    def authenticate_user(self, username: str, password: str):
        return au(username, password, self.repo)


def get_user_service(
    repo: Annotated[AbstractUserRepository, Depends(get_user_repo)]
) -> UserService:
    return UserService(repo)
