import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.db.database import Base
from app.api.db.models import User
from app.core.security import get_password_hash


DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def setup_test_db(async_session):
    for table in reversed(Base.metadata.sorted_tables):
        await async_session.execute(table.delete())
    await async_session.commit()
    user = User(
        username="existing_user",
        email="existing@example.com",
        hashed_password=get_password_hash("Password1!"),
    )
    async_session.add(user)
    await async_session.commit()
