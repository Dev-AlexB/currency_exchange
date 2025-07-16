import pytest

from app.api.errors.exceptions import (
    AuthorizationException,
    CustomException,
    ExternalAPIDataError,
    ExternalAPIHTTPError,
    InvalidTokenException,
    UniqueFieldException,
    UserUnauthorisedException,
)


def test_custom_exception():
    exc = CustomException("Кастомное исключение")
    assert exc.detail == "Кастомное исключение"


@pytest.mark.parametrize(
    "field, value, detail",
    [
        # ошибка неуникального username
        ("username", "john", "Имя пользователя 'john' уже используется"),
        # ошибка неуникального email
        (
            "email",
            "example@example.com",
            "Email 'example@example.com' уже используется",
        ),
        # ошибка неуникального другого поля
        (
            "some_field",
            "some_value",
            "Поле 'some_field' со значением 'some_value' уже используется",
        ),
    ],
    ids=[
        "Exception in username",
        "Exception in email",
        "Exception in some_field",
    ],
)
def test_unique_field_exception(field, value, detail):
    exc = UniqueFieldException(field, value)
    assert exc.field == field
    assert exc.value == value
    assert exc.detail == detail


def test_authorization_exception():
    exc = AuthorizationException("Ошибка авторизации")
    assert exc.detail == "Ошибка авторизации"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_user_unauthorised_exception():
    exc = UserUnauthorisedException()
    assert exc.detail == "Неверные учетные данные!"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_invalid_token_exception():
    exc = InvalidTokenException("Токен устарел")
    assert exc.detail == "Токен устарел"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_external_api_http_error():
    exc = ExternalAPIHTTPError(status_code=500, detail="Internal server error")
    assert exc.detail == "Internal server error"
    assert exc.status_code == 500


def test_external_api_data_error():
    key = "missing_key"
    data = {"some": "data"}
    exc = ExternalAPIDataError(key, data)
    assert key in str(exc)
    assert str(data) in str(exc)
