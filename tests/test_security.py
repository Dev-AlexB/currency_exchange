import datetime
from contextlib import nullcontext as does_not_raise

import jwt
import pytest

from app.api.errors.exceptions import InvalidTokenException
from app.core.config import settings
from app.core.security import (
    create_jwt_token,
    get_password_hash,
    get_username_from_token,
    verify_password,
)


# служебная функция - создает токен
def make_token(payload, secret=None):
    return jwt.encode(
        payload,
        secret or settings.JWT.SECRET_KEY,
        algorithm=settings.JWT.ALGORITHM,
    )


def test_password_hash_and_verify():
    password = "valid_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_create_jwt_token():
    data = {"sub": "test_username"}
    token = create_jwt_token(data)
    assert isinstance(token, str)
    decoded = jwt.decode(
        token, settings.JWT.SECRET_KEY, algorithms=[settings.JWT.ALGORITHM]
    )
    assert decoded["sub"] == "test_username"
    assert "exp" in decoded
    exp_timestamp = decoded["exp"]
    now_timestamp = datetime.datetime.now(datetime.UTC).timestamp()
    assert exp_timestamp > now_timestamp


@pytest.mark.parametrize(
    "payload, secret, expectation, error_detail",
    [
        # валидный токен
        (
            {
                "sub": "user",
                "exp": datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(minutes=5),
            },
            None,
            does_not_raise(),
            None,
        ),
        # токен истек
        (
            {
                "sub": "user",
                "exp": datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(seconds=1),
            },
            None,
            pytest.raises(InvalidTokenException),
            "Токен устарел",
        ),
        # неверная подпись
        (
            {
                "sub": "user",
                "exp": datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(minutes=5),
            },
            "wrong_secret",
            pytest.raises(InvalidTokenException),
            "Ошибка чтения токена",
        ),
    ],
    ids=["Valid token", "Expired token", "Wrong signature"],
)
def test_get_username_from_token(payload, secret, expectation, error_detail):
    token = make_token(payload, secret)
    with expectation as error:
        result = get_username_from_token(token)
        assert result == payload["sub"]
        if error_detail:
            assert str(error) == error_detail
