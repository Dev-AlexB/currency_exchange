from abc import ABC, abstractmethod

from app.api.errors.exceptions import InvalidUsernameException
from app.api.schemas.users import User, UserCreate, UserInDB
from app.core.security import get_password_hash


fake_db = {
    "admin": {
        "username": "admin",
        "password": "pass",
        "email": "admin@mail.ru",
        "hashed_password": "$2b$12$yd.0JNLmiWgkgReH8W8zDOZecGLLyRGSNHM42Q.O468YRkt2fkAt6",
    },
}


def get_user_from_db(username) -> UserInDB | None:
    user_dict = fake_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)


def add_user_to_db(user_new: UserCreate) -> User:
    name, password = user_new.username, user_new.password
    if not get_user_from_db(name):
        user_dict = user_new.model_dump(exclude={"password"})
        user_added = UserInDB(
            **user_dict, hashed_password=get_password_hash(password)
        )
        fake_db[name] = user_added.model_dump()
        return User(**user_dict)
    raise InvalidUsernameException(name)


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_user(self, username: str) -> UserInDB | None:
        pass

    @abstractmethod
    def add_user(self, user: User) -> User:
        pass


class FakeDatabase(AbstractUserRepository):
    def __init__(self, data: dict) -> None:
        self.data = data

    def get_user(self, username: str) -> UserInDB | None:
        username = username.lower()
        user_dict = self.data.get(username)
        if user_dict:
            return UserInDB(**user_dict)
        return None

    def add_user(self, user: UserCreate) -> User:
        name, password = user.username.lower(), user.password
        if not self.get_user(name):
            user_dict = user.model_dump(exclude={"password"})
            user_added = UserInDB(
                **user_dict, hashed_password=get_password_hash(password)
            )
            self.data[name] = user_added.model_dump()
            return User(**user_dict)
        raise InvalidUsernameException(name)


fake_db_repo = FakeDatabase(fake_db)
