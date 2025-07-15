from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, MappedColumn

from app.api.db.database import Base
from app.api.schemas.users import UserCreate
from app.core.security import get_password_hash


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = MappedColumn(
        BigInteger, primary_key=True, autoincrement=True, index=True
    )
    username: Mapped[str] = MappedColumn(
        String(50), unique=True, nullable=False
    )
    email: Mapped[str] = MappedColumn(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = MappedColumn(String(60), nullable=False)

    @classmethod
    def from_schema(cls, schema: UserCreate):
        hashed_password = get_password_hash(schema.password)
        data_dict = schema.model_dump(exclude={"password"})
        return cls(**data_dict, hashed_password=hashed_password)
