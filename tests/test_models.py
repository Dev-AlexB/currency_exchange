from app.api.db.models import User
from app.api.schemas.users import UserCreate


def test_user_from_schema(mocker):
    schema = UserCreate(
        username="test_user", email="test@email.com", password="1SecretPass!"
    )
    mock_hash = "hashed"
    mocker.patch("app.api.db.models.get_password_hash", return_value=mock_hash)
    user = User.from_schema(schema)
    assert user.username == "test_user"
    assert user.email == "test@email.com"
    assert user.hashed_password == mock_hash
    assert not hasattr(user, "password")
