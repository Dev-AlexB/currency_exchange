from typing import Any

import requests

from app.api.errors.exceptions import ExternalAPIHTTPError, ExternalAPIKeyError
from app.api.errors.logger import logger
from app.api.schemas.currency import (
    CurrencyList,
    CurrencyRequest,
    CurrencyResponse,
)
from app.core.config import settings


def ext_api_request(url: str, **kwargs) -> dict:
    response = requests.request(
        "GET",
        url.format(**kwargs),
        headers={"apikey": settings.CURRENCY.API_KEY},
    )
    st_code, text = response.status_code, response.text
    logger.debug(f"Запрос к внешнему API. Cтатус:{st_code}. {text}")
    if st_code == 200:
        return response.json()
    raise ExternalAPIHTTPError(status_code=st_code, detail=text)


def ext_api_get_data(data_dict: dict, key: str) -> Any:
    data = data_dict.get(key)
    if data:
        return data
    raise ExternalAPIKeyError(key=key, data_dict=data_dict)


def ext_api_get_currencies() -> CurrencyList:
    data_dict = ext_api_request(settings.CURRENCY.URL_LIST)
    currencies_dict = ext_api_get_data(data_dict=data_dict, key="currencies")
    return CurrencyList(currencies=currencies_dict)


def ext_api_get_exchange(currency: CurrencyRequest) -> CurrencyResponse:
    req_params = currency.model_dump()
    data_dict = ext_api_request(settings.CURRENCY.URL_EXCHANGE, **req_params)
    result = ext_api_get_data(data_dict=data_dict, key="result")
    return CurrencyResponse(**req_params, result=result)
