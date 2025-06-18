from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors.exceptions import (
    ExternalAPIHTTPError,
    ExternalAPIKeyError,
    InvalidTokenException,
    InvalidUsernameException,
    UserUnauthorisedException,
)


def test_invalid_username_exception():
    exc = InvalidUsernameException("occupied_username")
    assert exc.status_code == 400
    assert "Имя пользователя occupied_username" in exc.detail


def test_user_unauthorised_exception_default():
    exc = UserUnauthorisedException()
    assert exc.status_code == 401
    assert exc.detail == "Неверные учетные данные!"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_invalid_token_exception():
    exc = InvalidTokenException("Токен устарел")
    assert isinstance(exc, StarletteHTTPException)


def test_external_api_http_error():
    exc = ExternalAPIHTTPError(status_code=500, detail="Internal server error")
    assert isinstance(exc, StarletteHTTPException)


def test_external_api_key_error():
    key = "missing_key"
    data = {"some": "data"}
    exc = ExternalAPIKeyError(key, data)
    assert key in str(exc)
    assert str(data) in str(exc)
