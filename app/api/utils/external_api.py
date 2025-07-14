from typing import Any

import httpx

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


def ext_api_get_data(data_dict: dict, key: str) -> Any:
    if key in data_dict:
        return data_dict[key]
    raise ExternalAPIDataError(key=key, data_dict=data_dict)


async def ext_api_get_currencies() -> CurrencyAll:
    data_dict = await ext_api_request(settings.CURRENCY.URL_LIST)
    currencies_dict = ext_api_get_data(key="currencies", data_dict=data_dict)
    return CurrencyAll(currencies=currencies_dict)


async def ext_api_get_exchange(currency: CurrencyRequest) -> CurrencyResponse:
    req_params = currency.model_dump()
    data_dict = await ext_api_request(
        settings.CURRENCY.URL_EXCHANGE, **req_params
    )
    result = ext_api_get_data(key="result", data_dict=data_dict)
    return CurrencyResponse(**req_params, result=result)
