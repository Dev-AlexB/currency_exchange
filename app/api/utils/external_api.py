from typing import Any

import httpx
from pydantic import ValidationError

from app.api.errors.exceptions import (
    ExternalAPIDataError,
    ExternalAPIHTTPError,
)
from app.api.errors.logger import logger
from app.api.schemas.currency import (
    CurrencyAll,
    CurrencyRequest,
    CurrencyResponse,
)
from app.core.config import settings


async def ext_api_request(url: str, **kwargs) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url.format(**kwargs),
                headers={"apikey": settings.CURRENCY.API_KEY},
            )
    except httpx.RequestError as e:
        raise ExternalAPIHTTPError(detail=str(e)) from e
    else:
        st_code, text = response.status_code, response.text
        logger.debug(f"Запрос к внешнему API. Ответ с кодом {st_code}: {text}")
        if st_code == 200:
            return response.json()
        raise ExternalAPIHTTPError(status_code=st_code, detail=text)


def ext_api_get_data(key: str, data: dict) -> Any:
    try:
        result = data[key]
    except Exception as e:
        raise ExternalAPIDataError(
            detail=f"Ключ '{key}' не найден в JSON из внешнего API.",
            ext_api_data=data,
        ) from e
    return result


async def ext_api_get_currencies() -> CurrencyAll:
    data = await ext_api_request(settings.CURRENCY.URL_LIST)
    currencies_dict = ext_api_get_data(key="currencies", data=data)
    try:
        result = CurrencyAll(currencies=currencies_dict)
    except ValidationError as e:
        raise ExternalAPIDataError(
            detail="Ошибка валидации данных из внешнего API.",
            ext_api_data=currencies_dict,
        ) from e
    return result


async def ext_api_get_exchange(currency: CurrencyRequest) -> CurrencyResponse:
    req_params = currency.model_dump()
    data_dict = await ext_api_request(
        settings.CURRENCY.URL_EXCHANGE, **req_params
    )
    counted_result = ext_api_get_data(key="result", data=data_dict)
    try:
        result = CurrencyResponse(**req_params, result=counted_result)
    except ValidationError as e:
        raise ExternalAPIDataError(
            detail="Ошибка валидации данных из внешнего API.",
            ext_api_data=counted_result,
        ) from e
    return result
