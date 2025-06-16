from contextlib import nullcontext as does_not_raise

import pytest
from pytest_mock import MockerFixture

from app.api.db.services import UserService
from app.api.errors.exceptions import UserUnauthorisedException
from app.api.schemas.users import User, UserCreate, UserInDB
from app.core.security import get_password_hash


class TestUserService:
    def test_register_user(self, mocker: MockerFixture):
        mock_repo = mocker.Mock()
        user_service = UserService(mock_repo)
        user_input = UserCreate(
            username="valid_user",
            email="valid@email.com",
            password="valid_password",
        )
        user_return = User(username="valid_user", email="valid@email.com")
        mock_repo.add_user.return_value = user_return
        result = user_service.register_user(user_input)
        mock_repo.add_user.assert_called_once_with(user_input)
        assert result == user_return

    def test_read_user_from_db(self, mocker: MockerFixture):
        mock_repo = mocker.Mock()
        user_service = UserService(mock_repo)
        username = "valid_user"
        user_return = UserInDB(
            username="valid_user",
            email="valid@email.com",
            hashed_password="hashed",
        )
        mock_repo.get_user.return_value = user_return
        result = user_service.read_user_from_db(username)
        mock_repo.get_user.assert_called_once_with(username)
        assert result == user_return

    @pytest.mark.parametrize(
        "username, password, return_user, expectation",
        [
            # успешная аутентификация
            (
                "valid_user",
                "valid_pass",
                UserInDB(
                    username="valid_user",
                    email="valid@email.com",
                    hashed_password=get_password_hash("valid_pass"),
                ),
                does_not_raise(),
            ),
            # неправильный пароль
            (
                "valid_user",
                "wrong_pass",
                UserInDB(
                    username="valid_user",
                    email="valid@email.com",
                    hashed_password=get_password_hash("valid_pass"),
                ),
                pytest.raises(UserUnauthorisedException),
            ),
            # пользователь не найден
            (
                "not_in_base",
                "any",
                None,
                pytest.raises(UserUnauthorisedException),
            ),
        ],
        ids=[
            "Successful authentication",
            "Incorrect password",
            "User not found",
        ],
    )
    def test_authenticate_user(
        self, mocker, username, password, return_user, expectation
    ):
        mock_repo = mocker.Mock()
        mock_repo.get_user.return_value = return_user
        service = UserService(mock_repo)
        with expectation:
            result = service.authenticate_user(username, password)
            assert result == return_user
        mock_repo.get_user.assert_called_once_with(username)
