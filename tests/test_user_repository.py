import pytest
import pytest_asyncio
from pydantic import EmailStr, TypeAdapter
from sqlalchemy.exc import IntegrityError

from app.api.db.models import User
from app.api.repositories.user_repository import AlchemyUserRepository


@pytest_asyncio.fixture
async def user_repository(async_session):
    return AlchemyUserRepository(async_session)


@pytest.mark.asyncio
async def test_add_one_success(user_repository):
    user = User(
        username="testuser", email="test@example.com", hashed_password="hashed"
    )
    result = await user_repository.add_one(user)
    assert result.id is not None
    assert result.username == user.username


@pytest.mark.usefixtures("setup_test_db")
@pytest.mark.asyncio
async def test_add_one_duplicate_username(user_repository):
    user_with_same_username = User(
        username="existing_user",
        email="new@example.com",
        hashed_password="hashed",
    )
    with pytest.raises(IntegrityError):
        await user_repository.add_one(user_with_same_username)


@pytest.mark.usefixtures("setup_test_db")
@pytest.mark.asyncio
async def test_add_one_duplicate_email(user_repository):
    user_with_same_email = User(
        username="new", email="existing@example.com", hashed_password="hashed"
    )
    with pytest.raises(IntegrityError):
        await user_repository.add_one(user_with_same_email)


@pytest.mark.usefixtures("setup_test_db")
@pytest.mark.asyncio
async def test_get_by_username(user_repository):
    found = await user_repository.get_by_username("existing_user")
    assert found is not None
    assert found.email == "existing@example.com"

    not_found = await user_repository.get_by_username("not_existing")
    assert not_found is None


@pytest.mark.usefixtures("setup_test_db")
@pytest.mark.asyncio
async def test_get_by_email(user_repository):
    email_1 = TypeAdapter(EmailStr).validate_python("existing@example.com")
    found = await user_repository.get_by_email(email_1)
    assert found is not None
    assert found.username == "existing_user"

    email_2 = TypeAdapter(EmailStr).validate_python("not_existing@example.com")
    not_found = await user_repository.get_by_email(email_2)
    assert not_found is None
