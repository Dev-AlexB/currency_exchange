import pytest
from pytest_mock import MockerFixture

from app.api.db.UoW import UserUnitOfWork


@pytest.fixture
def mocked_session(mocker: MockerFixture):
    mock_session = mocker.AsyncMock()
    mocker.patch(
        "app.api.db.UoW.async_session_maker", return_value=mock_session
    )
    return mock_session


@pytest.mark.asyncio
async def test_uow_enter_sets_user_repo(mocked_session):
    uow = UserUnitOfWork()
    async with uow:
        pass
    assert uow.user_repo.session == mocked_session


@pytest.mark.asyncio
async def test_uow_exit_calls_commit_on_success(mocked_session):
    uow = UserUnitOfWork()
    async with uow:
        pass
    mocked_session.commit.assert_awaited_once()
    mocked_session.close.assert_awaited_once()
    mocked_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_uow_exit_calls_rollback_on_exception(mocked_session):
    uow = UserUnitOfWork()
    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("Some error")
    mocked_session.rollback.assert_awaited_once()
    mocked_session.close.assert_awaited_once()
    mocked_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_uow_commit_delegates_to_session(mocked_session):
    uow = UserUnitOfWork()
    async with uow:
        await uow.commit()
    mocked_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_uow_rollback_delegates_to_session(mocked_session):
    uow = UserUnitOfWork()
    async with uow:
        await uow.rollback()
    mocked_session.rollback.assert_awaited()
