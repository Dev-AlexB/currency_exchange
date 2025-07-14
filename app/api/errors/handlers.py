import json

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.errors.exceptions import (
    AuthorizationException,
    ExternalAPIDataError,
    ExternalAPIHTTPError,
    UniqueFieldException,
)
from app.api.errors.logger import logger


def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обрабатывает и логгирует все необработанные ошибки.

    Обрабатывает ошибки, не обработанные другими хендлерами.
    """

    message = (
        f"Вызвано не задокументированное исключение "
        f"{type(exc).__name__}: {exc}."
    )
    # передать exc_info=True, чтобы включить инфу об ошибке (fastapi сам кидает в консоль)
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Внутренняя ошибка сервера."},
    )


def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки валидации данных клиента."""

    message = (
        f"Вызвано исключение {type(exc).__name__}.\n"
        f"Ошибки: {exc.errors()}\n"
        f"Тело запроса, вызвавшего ошибку: {exc.body}"
    )
    logger.error(message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Ошибка валидации данных клиента.",
            "errors": exc.errors(),
            "body": (
                json.dumps(exc.body, ensure_ascii=False, indent=2)
                if exc.body
                else None
            ),
        },
    )


def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Обрабатывает и логгирует внутренние ошибки валидации."""

    message = (
        f"Вызвано исключение {type(exc).__name__}.\n" f"Ошибки: {exc.errors()}"
    )
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Внутренняя ошибка сервера."},
    )


def external_api_http_error_handler(
    request: Request, exc: ExternalAPIHTTPError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки внешнего API.

    Обрабатывает ошибки внешнего API, возникающие когда внешний API
    возвращает код отличный от 200, или когда ошибка возникает в самом
    запросе к внешнему API (библиотека requests).
    """

    base_message = f"Вызвано исключение {type(exc).__name__}: {exc}."
    if exc.__cause__:
        cause_type = type(exc.__cause__)
        full_message = (
            f"{base_message}\n"
            f"Причина: {cause_type.__module__}.{cause_type.__name__}: "
            f"{exc.__cause__}"
        )
        # если писать лог в файл, то logger.exception,
        # чтобы не потерять traceback (в консоль FastApi и так кидает)
        logger.error(full_message)
    else:
        full_message = (
            f"{base_message}\n"
            f"Статус-код ответа внешнего API: {exc.status_code}. "
            f"Текст ответа: {exc.detail}"
        )
        if exc.status_code == 402:
            logger.error(full_message)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": "Код валюты не найден. "
                    "Для проверки доступных кодов воспользуйтесь URL "
                    "currency/list"
                },
            )
        logger.critical(full_message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Проблема с ответом внешнего API"},
    )


def external_api_data_error_handler(
    request: Request, exc: ExternalAPIDataError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки в данных внешнего API."""

    message = f"Вызвано исключение {type(exc).__name__}: {exc}"
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Проблема с ответом внешнего API"},
    )


def unique_field_exception_handler(
    request: Request, exc: UniqueFieldException
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки UniqueFieldException.

    Эти ошибки возникают при попытке добавить пользователя со значением
    уже содержащимся в БД в поле, для которого значения уникальны.
    """

    message = f"Вызвано исключение {type(exc).__name__}: {exc}."
    logger.error(message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc)},
    )


def authorization_exception_handler(
    request: Request, exc: AuthorizationException
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки авторизации.

    Обрабатывает ошибку UserUnauthorisedException при вводе неверного
    логина/пароля и ошибку InvalidTokenException, возникающую
    если токен просрочен или декодируется с ошибкой.
    """

    base_message = f"Вызвано исключение {type(exc).__name__}: {exc}."
    if exc.__cause__:
        cause_type = type(exc.__cause__)
        full_message = (
            f"{base_message}\n"
            f"Причина: {cause_type.__module__}.{cause_type.__name__}: "
            f"{exc.__cause__}"
        )
        # если писать лог в файл, то logger.exception,
        # чтобы не потерять traceback (в консоль FastApi и так кидает)
        logger.error(full_message)
    else:
        logger.error(base_message)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": str(exc)},
        headers=exc.headers,
    )


handlers = {
    RequestValidationError: request_validation_error_handler,
    ValidationError: validation_error_handler,
    ResponseValidationError: validation_error_handler,
    ExternalAPIHTTPError: external_api_http_error_handler,
    ExternalAPIDataError: external_api_data_error_handler,
    UniqueFieldException: unique_field_exception_handler,
    AuthorizationException: authorization_exception_handler,
    Exception: global_exception_handler,
}
