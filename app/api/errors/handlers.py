from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors.exceptions import ExternalAPIError
from app.api.errors.logger import logger


def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки HTTP."""

    message = (
        f"Вызвано исключение HTTPException. "
        f"Статус-код: {exc.status_code}. "
        f"Детали:\n{exc.detail}"
    )
    logger.exception(message)
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
        f"Вызвано исключение RequestValidationError. Ошибки:\n"
        f'{'\n'.join(map(str, exc.errors()))}\n'
        f"Тело запроса, вызвавшего ошибку:\n{exc.body}"
    )
    logger.exception(message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Ошибка валидации отправленных данных.",
            "errors": exc.errors(),
            "body": exc.body,
        },
    )


def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Обрабатывает и логгирует внутренние ошибки валидации."""

    message = (
        f"Вызвано исключение ValidationError. Ошибки:\n"
        f'{'\n'.join(map(str, exc.errors()))}'
    )
    logger.exception(message)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Внутренняя ошибка сервера."},
    )


def external_api_error_handler(
    request: Request, exc: ExternalAPIError
) -> JSONResponse:
    """Обрабатывает и логгирует ошибки внешнего API."""

    message = (
        f"Вызвано исключение ExternalAPIError."
        f"Статус-код ответа внешнего API: {exc.status_code}. "
        f"Текст ответа:\n{exc.detail}"
    )
    logger.exception(message)
    if exc.status_code == 402:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "message": "Код валюты не найден. "
                "Для проверки доступных кодов воспользуйтесь URL "
                "currency/list"
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Проблема с ответом внешнего API"},
    )


handlers = {
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: request_validation_error_handler,
    ValidationError: validation_error_handler,
    ExternalAPIError: external_api_error_handler,
}
