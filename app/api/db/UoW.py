from typing import Protocol, Self, runtime_checkable

from app.api.db.database import async_session_maker
from app.api.repositories.user_repository import (
    AlchemyUserRepository,
    IUserRepository,
)


@runtime_checkable
class IUserUnitOfWork(Protocol):
    user_repo: IUserRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class UserUnitOfWork:
    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()
        self.user_repo = AlchemyUserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self) -> None:
        self.session.commit()

    async def rollback(self) -> None:
        self.session.rollback()
