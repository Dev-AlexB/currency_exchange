import requests
from fastapi import status

from app.api.errors.exceptions import ExternalAPIError
from app.api.errors.logger import logger
from app.api.schemas.currency import (
    CurrencyList,
    CurrencyRequest,
    CurrencyResponse,
)
from app.core.config import settings


def ext_api_request(url: str, **kwargs):
    response = requests.request(
        "GET",
        url.format(**kwargs),
        headers={"apikey": settings.CURRENCY.API_KEY},
    )
    st_code, text = response.status_code, response.text
    logger.debug(f"Запрос к внешнему API. Cтатус:{st_code}. {text}")
    if response.status_code == 200:
        return response.json()
    raise ExternalAPIError(status_code=st_code, detail=text)


def ext_api_get_currencies() -> CurrencyList:
    data = ext_api_request(settings.CURRENCY.URL_LIST)
    currencies_dict = data.get("currencies")
    if not currencies_dict:
        raise ExternalAPIError(
            status_code=status.HTTP_200_OK,
            detail='Ключ "currencies" не найден в JSON из внешнего API'
            f"Ответ внешнего API: {data}",
        )
    return CurrencyList(currencies=currencies_dict)


def ext_api_get_exchange(currency: CurrencyRequest) -> CurrencyResponse:
    req_params = currency.model_dump()
    data = ext_api_request(settings.CURRENCY.URL_EXCHANGE, **req_params)
    result = data.get("result")
    if not result:
        raise ExternalAPIError(
            status_code=status.HTTP_200_OK,
            detail='Ключ "result" не найден в JSON из внешнего API'
            f"Ответ внешнего API: {data}",
        )
    return CurrencyResponse(**req_params, result=result)
