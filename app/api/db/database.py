from abc import ABC, abstractmethod

from app.api.errors.exceptions import InvalidUsernameException
from app.api.schemas.users import User, UserCreate, UserInDB
from app.core.security import get_password_hash


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_user(self, username: str) -> UserInDB | None:
        pass

    @abstractmethod
    def add_user(self, user: UserCreate) -> User:
        pass


class FakeDatabase(AbstractUserRepository):
    data = {
        "admin": {
            "username": "admin",
            "password": "password",
            "email": "admin@mail.ru",
            "hashed_password": "$2b$12$yd.0JNLmiWgkgReH8W8zDOZecGLLyRGSNHM42Q.O468YRkt2fkAt6",
        },
    }

    def get_user(self, username: str) -> UserInDB | None:
        username = username.lower()
        user_dict = self.__class__.data.get(username)
        if user_dict:
            return UserInDB(**user_dict)
        return None

    def add_user(self, user: UserCreate) -> User:
        name, password = user.username.lower(), user.password
        if not self.get_user(name):
            user_dict = {
                key: value.lower()
                for key, value in user.model_dump(exclude={"password"}).items()
            }
            user_added = UserInDB(
                **user_dict, hashed_password=get_password_hash(password)
            )
            self.__class__.data[name] = user_added.model_dump()
            return User(**user_dict)
        raise InvalidUsernameException(name)


def get_user_repo() -> AbstractUserRepository:
    return FakeDatabase()
