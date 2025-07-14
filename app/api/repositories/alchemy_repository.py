from typing import Generic, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db.database import Base


AlchemyModel = TypeVar("AlchemyModel", bound=Base)


class AlchemyRepository(Generic[AlchemyModel]):
    model = Type[AlchemyModel]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
