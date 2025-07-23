import json
from contextlib import nullcontext as does_not_raise
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pytest_mock import MockerFixture

from app.api.errors.exceptions import (
    ExternalAPIDataError,
    ExternalAPIHTTPError,
)
from app.api.schemas.currency import (
    CurrencyAll,
    CurrencyRequest,
    CurrencyResponse,
)
from app.api.utils.external_api import (
    ext_api_get_currencies,
    ext_api_get_data,
    ext_api_get_exchange,
    ext_api_request,
)
from app.core.config import settings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, response_json, expectation",
    [
        (200, {"key": "value"}, does_not_raise()),
        (
            401,
            {"message": "Unauthorized"},
            pytest.raises(ExternalAPIHTTPError),
        ),
        (
            500,
            {"message": "Internal server error"},
            pytest.raises(ExternalAPIHTTPError),
        ),
    ],
    ids=[
        "Successful request",
        "Unauthorized (no valid API key)",
        "Server error on external api",
    ],
)
async def test_ext_api_request(
    mocker: MockerFixture, status, response_json, expectation
):
    mock_response = AsyncMock()
    mock_response.status_code = status
    mock_response.json = Mock(return_value=response_json)
    mock_response.text = json.dumps(response_json)
    mock_get = mocker.patch(
        "httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)
    )
    with expectation as exc_info:
        result = await ext_api_request("fake_api_url")
    if status == 200:
        assert result == response_json
    else:
        assert exc_info.value.detail == json.dumps(response_json)
        assert exc_info.value.status_code == status
    mock_get.assert_awaited_once_with(
        "fake_api_url", headers={"apikey": settings.CURRENCY.API_KEY}
    )


@pytest.mark.asyncio
async def test_ext_api_request_network_error(mocker: MockerFixture):
    mocker.patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(
            side_effect=httpx.RequestError("Connection failed"),
        ),
    )
    with pytest.raises(
        ExternalAPIHTTPError, match="Connection failed"
    ) as exc_info:
        await ext_api_request("url")
    error = exc_info.value
    assert error.status_code is None
    assert isinstance(error.__cause__, httpx.RequestError)
    assert str(error.__cause__) == "Connection failed"


def test_ext_api_get_data_success():
    assert ext_api_get_data(data={"key": "value"}, key="key") == "value"


def test_ext_api_get_data_missing_key():
    with pytest.raises(ExternalAPIDataError, match=r"missing_key"):
        ext_api_get_data(data={}, key="missing_key")


@pytest.mark.asyncio
async def test_ext_api_get_currencies_success(mocker: MockerFixture):
    mock_data = {"currencies": {"USD": "United States Dollar", "EUR": "Euro"}}
    mock_ext_api = mocker.patch(
        "app.api.utils.external_api.ext_api_request",
        new_callable=AsyncMock,
        return_value=mock_data,
    )
    result = await ext_api_get_currencies()
    assert result == CurrencyAll(**mock_data)
    mock_ext_api.assert_awaited_once_with(settings.CURRENCY.URL_LIST)


@pytest.mark.parametrize(
    "mock_return, detail",
    [
        (
            {},
            "Ключ 'currencies' не найден в JSON из внешнего API.",
        ),
        (
            {"currencies": {}},
            "Ошибка валидации данных из внешнего API.",
        ),
    ],
    ids=["Missing key", "Validation error"],
)
@pytest.mark.asyncio
async def test_ext_api_get_currencies_missing_key(
    mocker: MockerFixture, mock_return, detail
):
    mocker.patch(
        "app.api.utils.external_api.ext_api_request",
        new_callable=AsyncMock,
        return_value=mock_return,
    )
    with pytest.raises(ExternalAPIDataError) as exc_info:
        await ext_api_get_currencies()
    assert str(exc_info.value) == detail


@pytest.mark.asyncio
async def test_ext_api_get_exchange_success(mocker: MockerFixture):
    currency_req = CurrencyRequest(
        currency_1="USD", currency_2="EUR", amount=100
    )
    mock_response_data = {"result": 93}
    mock_ext_api = mocker.patch(
        "app.api.utils.external_api.ext_api_request",
        new_callable=AsyncMock,
        return_value=mock_response_data,
    )
    result = await ext_api_get_exchange(currency_req)
    assert result == CurrencyResponse(
        currency_1="USD", currency_2="EUR", amount=100, result=93
    )
    mock_ext_api.assert_awaited_once_with(
        settings.CURRENCY.URL_EXCHANGE,
        currency_1="USD",
        currency_2="EUR",
        amount=100,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_response_data, detail",
    [
        # отсутствует ключ result
        ({}, "Ключ 'result' не найден в JSON из внешнего API."),
        # значение по ключу result не число
        (
            {"result": "not_a_number"},
            "Ошибка валидации данных из внешнего API.",
        ),
    ],
    ids=[
        "Missing key 'result'",
        "Validation error in data from external API",
    ],
)
async def test_ext_api_get_exchange_error_cases(
    mocker: MockerFixture, mock_response_data, detail
):
    currency_req = CurrencyRequest(
        currency_1="USD", currency_2="EUR", amount=100
    )
    mocker.patch(
        "app.api.utils.external_api.ext_api_request",
        new_callable=AsyncMock,
        return_value=mock_response_data,
    )
    with pytest.raises(ExternalAPIDataError) as exc_info:
        await ext_api_get_exchange(currency_req)
    assert str(exc_info.value) == detail
