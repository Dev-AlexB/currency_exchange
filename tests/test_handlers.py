import json

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from app.api.errors.exceptions import (
    ExternalAPIDataError,
    ExternalAPIHTTPError,
    InvalidTokenException,
    UniqueFieldException,
    UserUnauthorisedException,
)
from app.api.errors.handlers import (
    authorization_exception_handler,
    external_api_data_error_handler,
    external_api_http_error_handler,
    global_exception_handler,
    request_validation_error_handler,
    unique_field_exception_handler,
    validation_error_handler,
)


def test_global_exception_handler(caplog):
    request = Request(scope={"type": "http"})
    exc = ValueError("unexpected value")
    with caplog.at_level("CRITICAL"):
        response = global_exception_handler(request, exc)
    assert response.status_code == 500
    body_dict = json.loads(response.body)
    assert body_dict == {"message": "Внутренняя ошибка сервера."}
    assert "ValueError" in caplog.text


def test_request_validation_error_handler(caplog):
    request = Request(scope={"type": "http"})
    errors = [
        {
            "loc": ["body", "field"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
    exc = RequestValidationError(errors)
    exc.body = {"some": "body"}
    with caplog.at_level("ERROR"):
        response = request_validation_error_handler(request, exc)
    assert response.status_code == 422
    body_dict = json.loads(response.body)
    assert body_dict["message"] == "Ошибка валидации данных клиента."
    assert body_dict["errors"] == errors
    assert "RequestValidationError" in caplog.text
    assert "field required" in caplog.text
    assert str(exc.body) in caplog.text


def test_validation_error_handler(caplog):
    class DummyModel(BaseModel):
        name: str

    request = Request(scope={"type": "http"})
    try:
        DummyModel(name=123)  # noqa: тут специально name некорректного типа
    except ValidationError as exc:
        with caplog.at_level("CRITICAL"):
            response = validation_error_handler(request, exc)
    assert response.status_code == 500
    body_dict = json.loads(response.body)
    assert body_dict["message"] == "Внутренняя ошибка сервера."
    assert "ValidationError" in caplog.text
    assert "Input should be a valid string" in caplog.text


@pytest.mark.parametrize(
    "status_code, detail, cause, "
    "expected_status, expected_message_part, log_level",
    [
        # ошибка с причиной __cause__ (log в "exception")
        (
            500,
            "Timed out",
            Exception("Timed out"),
            500,
            "Проблема с ответом внешнего API",
            "EXCEPTION",
        ),
        # не верный код валюты (log в "error")
        (
            402,
            "Currency code not found",
            None,
            400,
            "Код валюты не найден.",
            "ERROR",
        ),
        # любая другая ошибка в ответе внешнего API (log в "critical")
        (
            503,
            "Service unavailable",
            None,
            500,
            "Проблема с ответом внешнего API",
            "CRITICAL",
        ),
    ],
    ids=[
        "Exception in requests (no response from external API)",
        "Status 402 from external API",
        "All other non 200 statuses from external API",
    ],
)
def test_external_api_http_error_handler(
    caplog,
    status_code,
    detail,
    cause,
    expected_status,
    expected_message_part,
    log_level,
):
    request = Request(scope={"type": "http"})
    exc = ExternalAPIHTTPError(detail=detail, status_code=status_code)
    if cause:
        exc.__cause__ = cause
    with caplog.at_level("DEBUG"):
        response = external_api_http_error_handler(request, exc)
    assert response.status_code == expected_status
    assert expected_message_part in response.body.decode("utf-8")
    if log_level == "EXCEPTION":
        assert "Причина" in caplog.text
    else:
        assert detail in caplog.text
        assert log_level in caplog.text


def test_external_api_data_error_handler(caplog):
    request = Request(scope={"type": "http"})
    detail = "Ключ 'currencies' не найде в ответе внешнего API"
    ext_api_data = {"some": "data"}
    exc = ExternalAPIDataError(detail=detail, ext_api_data=ext_api_data)
    exc.__cause__ = Exception("UH-oh!")
    with caplog.at_level("CRITICAL"):
        response = external_api_data_error_handler(request, exc)
    assert response.status_code == 500
    body_dict = json.loads(response.body)
    assert body_dict["message"] == "Проблема с ответом внешнего API"
    assert "ExternalAPIDataError" in caplog.text
    assert detail in caplog.text
    assert str(ext_api_data) in caplog.text
    assert repr(exc.__cause__) in caplog.text


def test_unique_field_exception_handler(caplog):
    request = Request(scope={"type": "http"})
    field = "username"
    value = "used_name"
    exc = UniqueFieldException(field, value)
    with caplog.at_level("ERROR"):
        response = unique_field_exception_handler(request, exc)
    body_dict = json.loads(response.body)
    assert response.status_code == 400
    assert body_dict["message"] == (
        f"Имя пользователя '{value}' уже используется"
    )


@pytest.mark.parametrize(
    "exc_type, detail, cause",
    [
        (
            UserUnauthorisedException,
            None,
            None,
        ),
        (
            InvalidTokenException,
            "Токен устарел",
            Exception("Signature expired"),
        ),
    ],
    ids=[
        "UserUnauthorisedException",
        "InvalidTokenException",
    ],
)
def test_authorization_exception_handler(caplog, exc_type, detail, cause):
    request = Request(scope={"type": "http"})
    exc = exc_type(detail=detail) if detail else exc_type()
    if cause:
        exc.__cause__ = cause
    with caplog.at_level("ERROR"):
        response = authorization_exception_handler(request, exc)
    body_dict = json.loads(response.body)
    assert response.status_code == 401
    assert body_dict["message"] == detail or "Неверные учетные данные!"
    assert response.headers.get("www-authenticate") == "Bearer"
    if cause:
        assert "Причина" in caplog.text
    if detail:
        assert detail in caplog.text
    else:
        assert "Неверные учетные данные!" in caplog.text
