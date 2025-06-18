from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors.exceptions import ExternalAPIHTTPError, ExternalAPIKeyError
from app.api.errors.logger import logger


def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обрабатывает и логгирует все необработанные ошибки.

    Обрабатывает ошибки, не обработанные другими хендлерами.
    """

    message = f"Вызвано незадокументированное исключение {type(exc).__name__}."
    # передать exc_info=True, чтобы включить инфу об ошибке (fastapi сам кидает в консоль)
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Внутренняя ошибка сервера."},
    )


def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки HTTP.

    Перехватывает, в том числе InvalidUsernameException,
    UserUnauthorisedException, InvalidTokenException.
    """

    message = (
        f"Вызвано исключение {type(exc).__name__}. "
        f"Статус-код: {exc.status_code}. "
        f"Детали:\n{exc.detail}"
    )
    logger.error(message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"Ошибка {exc.status_code} - {exc.detail}"},
        headers=exc.headers,
    )


def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки валидации данных клиента."""

    message = (
        f"Вызвано исключение {type(exc).__name__}. Ошибки:\n"
        f'{'\n'.join(map(str, exc.errors()))}\n'
        f"Тело запроса, вызвавшего ошибку:\n{exc.body}"
    )
    logger.error(message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Ошибка валидации отправленных клиентом данных.",
            "errors": exc.errors(),
            "body": str(exc.body),
        },
    )


def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Обрабатывает и логгирует внутренние ошибки валидации."""

    message = (
        f"Вызвано исключение {type(exc).__name__}. Ошибки:\n"
        f'{'\n'.join(map(str, exc.errors()))}'
    )
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Внутренняя ошибка сервера."},
    )


def external_api_http_error_handler(
    request: Request, exc: ExternalAPIHTTPError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки внешнего API."""

    base_message = f"Вызвано исключение {type(exc).__name__}."
    if exc.__cause__:
        exc_type = type(exc.__cause__)
        logger.exception(
            f"{base_message}\n"
            f"Причина:\n"
            f"Тип:{exc_type.__module__}.{exc_type.__name__}\n"
            f"Сообщение: {exc.__cause__}"
        )
    else:
        full_message = (
            f"{base_message} "
            f"Статус-код ответа внешнего API: {exc.status_code}. "
            f"Текст ответа:\n{exc.detail}"
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


def external_api_key_error_handler(
    request: Request, exc: ExternalAPIKeyError
) -> JSONResponse:
    message = f"Вызвано исключение {type(exc).__name__}: {exc.message}"
    logger.critical(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Проблема с ответом внешнего API"},
    )


handlers = {
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: request_validation_error_handler,
    ValidationError: validation_error_handler,
    ResponseValidationError: validation_error_handler,
    ExternalAPIHTTPError: external_api_http_error_handler,
    ExternalAPIKeyError: external_api_key_error_handler,
    Exception: global_exception_handler,
}
