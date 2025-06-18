import json

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from app.api.errors.exceptions import (
    ExternalAPIHTTPError,
    ExternalAPIKeyError,
    InvalidTokenException,
    InvalidUsernameException,
    UserUnauthorisedException,
)
from app.api.errors.handlers import (
    external_api_http_error_handler,
    external_api_key_error_handler,
    global_exception_handler,
    http_exception_handler,
    request_validation_error_handler,
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


@pytest.mark.parametrize(
    "exception, exc_name",
    [
        (
            InvalidUsernameException("occupied_username"),
            "InvalidUsernameException",
        ),
        (UserUnauthorisedException(), "UserUnauthorisedException"),
        (InvalidTokenException("Токен устарел"), "InvalidTokenException"),
    ],
    ids=[
        "InvalidUsernameException",
        "UserUnauthorisedException",
        "InvalidTokenException",
    ],
)
def test_http_exception_handler(caplog, exception, exc_name):
    request = Request(scope={"type": "http"})
    exc = exception
    with caplog.at_level("ERROR"):
        response = http_exception_handler(request, exc)
    assert response.status_code == exception.status_code
    body_dict = json.loads(response.body)
    assert exception.detail in body_dict["message"]
    assert exc_name in caplog.text


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
    assert (
        body_dict["message"]
        == "Ошибка валидации отправленных клиентом данных."
    )
    assert body_dict["errors"] == errors
    assert body_dict["body"] == str(exc.body)
    assert "RequestValidationError" in caplog.text
    assert "field required" in caplog.text
    assert str(exc.body) in caplog.text


def test_validation_error_handler(caplog):
    class DummyModel(BaseModel):
        name: str

    request = Request(scope={"type": "http"})
    try:
        DummyModel(name=123)
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
    exc = ExternalAPIHTTPError(status_code=status_code, detail=detail)
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


def test_external_api_key_error_handler(caplog):
    request = Request(scope={"type": "http"})
    key = "currencies"
    data_dict = {"some": "data"}
    exc = ExternalAPIKeyError(key=key, data_dict=data_dict)
    with caplog.at_level("CRITICAL"):
        response = external_api_key_error_handler(request, exc)
    assert response.status_code == 500
    body_dict = json.loads(response.body)

    assert body_dict["message"] == "Проблема с ответом внешнего API"
    assert "ExternalAPIKeyError" in caplog.text
    assert key in caplog.text
    assert str(data_dict) in caplog.text
