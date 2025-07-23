from contextlib import nullcontext as does_not_raise
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.db.models import User
from app.api.errors.exceptions import (
    UniqueFieldException,
    UserUnauthorisedException,
)
from app.api.schemas.users import UserCreate
from app.api.services.user_service import UserService


@pytest.mark.asyncio
async def test_register_user_success():
    user_create = UserCreate(
        username="test_user",
        email="test@example.com",  # type:ignore
        password="Secret1!",
    )
    uow = MagicMock()
    uow.__aenter__.return_value = uow
    uow.user_repo.get_by_username = AsyncMock(return_value=None)
    uow.user_repo.get_by_email = AsyncMock(return_value=None)
    dummy_user = User(
        id=1,
        username="test_user",
        email="test@example.com",
        hashed_password="hashed",
    )
    uow.user_repo.add_one = AsyncMock(return_value=dummy_user)
    service = UserService(uow)  # type: ignore
    result = await service.register_user(user_create)
    assert result.username == "test_user"
    assert result.email == "test@example.com"
    uow.user_repo.add_one.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("expected_field", ["username", "email"])
async def test_register_user_unique_constraints(expected_field):
    user_create = UserCreate(
        username="test_user",
        email="test@example.com",  # type:ignore
        password="Secret1!",
    )
    uow = MagicMock()
    uow.__aenter__.return_value = uow
    uow.user_repo.get_by_username = AsyncMock(
        return_value=User() if expected_field == "username" else None
    )
    uow.user_repo.get_by_email = AsyncMock(
        return_value=User() if expected_field == "email" else None
    )
    service = UserService(uow)  # type: ignore
    with pytest.raises(UniqueFieldException) as exc_info:
        await service.register_user(user_create)
    assert getattr(user_create, expected_field) in str(exc_info.value)


@pytest.mark.parametrize(
    "user_or_none, expectation, verified",
    [
        (
            User(username="test", hashed_password="hashed"),
            does_not_raise(),
            True,
        ),
        (
            User(username="test", hashed_password="hashed"),
            pytest.raises(UserUnauthorisedException),
            False,
        ),
        (None, pytest.raises(UserUnauthorisedException), False),
    ],
    ids=["Success", "Wrong password", "User not found"],
)
@pytest.mark.asyncio
async def test_authenticate_user_success(
    mocker, user_or_none, expectation, verified
):
    mocked_verify_password = mocker.patch(
        "app.api.services.user_service.verify_password", return_value=verified
    )
    uow = MagicMock()
    uow.__aenter__.return_value = uow
    uow.user_repo.get_by_username = AsyncMock(return_value=user_or_none)
    service = UserService(uow)  # type: ignore
    with expectation as exc_info:
        result = await service.authenticate_user("Test", "secret")
    if exc_info is None:
        assert result == "test"
    uow.user_repo.get_by_username.assert_awaited_once_with("test")
    if user_or_none is None:
        mocked_verify_password.assert_not_called()
    else:
        mocked_verify_password.assert_called_once_with("secret", "hashed")
