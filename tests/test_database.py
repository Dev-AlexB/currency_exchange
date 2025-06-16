import pytest

from app.api.db.database import get_user_repo
from app.api.errors.exceptions import InvalidUsernameException
from app.api.schemas.users import User, UserCreate


@pytest.fixture
def repo():
    return get_user_repo()


class TestFakeDatabase:
    def test_get_user(self, repo):
        admin_user = repo.get_user("Admin")
        assert admin_user.username == "admin"
        assert repo.get_user("invalid_user") is None

    def test_add_user(self, repo):
        return_user = repo.add_user(
            UserCreate(
                username="Valid_user",
                email="valid@email.com",
                password="valid_password",
            )
        )
        assert return_user == User(
            username="valid_user", email="valid@email.com"
        )
        assert repo.data["valid_user"] is not None
        assert not hasattr(return_user, "password")
        assert not hasattr(return_user, "hashed_password")

        old_email = repo.data["admin"]["email"]
        with pytest.raises(InvalidUsernameException):
            repo.add_user(
                UserCreate(
                    username="admin",
                    email="valid@email.com",
                    password="valid_password",
                )
            )
        assert repo.data["admin"]["email"] == old_email
