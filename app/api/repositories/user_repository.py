from typing import Optional, Protocol, Type, runtime_checkable

from pydantic import EmailStr
from sqlalchemy import select

from app.api.db.models import User
from app.api.repositories.alchemy_repository import AlchemyRepository


@runtime_checkable
class IUserRepository(Protocol):
    model = Type[User]

    async def add_one(self, user: User) -> User: ...
    async def get_by_username(self, username: str) -> Optional[User]: ...
    async def get_by_email(self, email: EmailStr) -> Optional[User]: ...


class AlchemyUserRepository(AlchemyRepository):
    model = User

    async def add_one(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(self.model).where(self.model.username == username)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_email(self, email: EmailStr) -> Optional[User]:
        stmt = select(self.model).where(self.model.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
