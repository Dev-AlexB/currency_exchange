import json
from contextlib import nullcontext as does_not_raise

import pytest
import requests
from pydantic import ValidationError
from pytest_mock import MockerFixture

import app
from app.api.errors.exceptions import ExternalAPIHTTPError, ExternalAPIKeyError
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
def test_ext_api_request(
    mocker: MockerFixture, status, response_json, expectation
):
    mock_response = mocker.Mock()
    mock_response.status_code = status
    mock_response.json.return_value = response_json
    mock_response.text = json.dumps(response_json)
    mocker.patch("requests.request", return_value=mock_response)
    with expectation as exc_info:
        result = ext_api_request("url")
    if status == 200:
        assert result == response_json
    else:
        assert isinstance(exc_info.value, ExternalAPIHTTPError)
        assert exc_info.value.detail == json.dumps(response_json)
        assert exc_info.value.status_code == status
    requests.request.assert_called_once_with(
        "GET", "url", headers={"apikey": settings.CURRENCY.API_KEY}
    )


def test_ext_api_request_request_exception(mocker: MockerFixture):
    mocker.patch(
        "requests.request",
        side_effect=requests.exceptions.Timeout("Timed out"),
    )
    with pytest.raises(ExternalAPIHTTPError) as exc_info:
        ext_api_request("url")
    error = exc_info.value
    assert error.status_code == 500
    assert "Timed out" in error.detail
    assert isinstance(error.__cause__, requests.exceptions.Timeout)
    assert str(error.__cause__) == "Timed out"


def test_ext_api_get_data_success():
    assert ext_api_get_data({"key": "value"}, "key") == "value"


def test_ext_api_get_data_missing_key():
    with pytest.raises(ExternalAPIKeyError, match=r"missing.*\{\}"):
        ext_api_get_data({}, "missing")


def test_ext_api_get_currencies_success(mocker: MockerFixture):
    mock_data = {"currencies": {"USD": "United States Dollar", "EUR": "Euro"}}
    mocker.patch(
        "app.api.utils.external_api.ext_api_request", return_value=mock_data
    )
    result = ext_api_get_currencies()
    assert result == CurrencyAll(**mock_data)
    app.api.utils.external_api.ext_api_request.assert_called_once_with(
        settings.CURRENCY.URL_LIST
    )


def test_ext_api_get_currencies_missing_key(mocker: MockerFixture):
    mocker.patch("app.api.utils.external_api.ext_api_request", return_value={})
    with pytest.raises(ExternalAPIKeyError, match=r"currencies.*\{\}"):
        ext_api_get_currencies()


def test_ext_api_get_currencies_validation_error(mocker: MockerFixture):
    mock_data = {"currencies": {}}
    mocker.patch(
        "app.api.utils.external_api.ext_api_request", return_value=mock_data
    )
    with pytest.raises(ValidationError):
        ext_api_get_currencies()


def test_ext_api_get_exchange_success(mocker: MockerFixture):
    currency_req = CurrencyRequest(
        currency_1="USD", currency_2="EUR", amount=100
    )
    mock_response_data = {"result": 93}
    mocker.patch(
        "app.api.utils.external_api.ext_api_request",
        return_value=mock_response_data,
    )
    result = ext_api_get_exchange(currency_req)
    assert result == CurrencyResponse(
        currency_1="USD", currency_2="EUR", amount=100, result=93
    )
    app.api.utils.external_api.ext_api_request.assert_called_once_with(
        settings.CURRENCY.URL_EXCHANGE,
        currency_1="USD",
        currency_2="EUR",
        amount=100,
    )


@pytest.mark.parametrize(
    "mock_response_data, expectation, side_effect",
    [
        # отсутствует ключ result
        ({}, pytest.raises(ExternalAPIKeyError), None),
        # значение по ключу result не число
        ({"result": "not_a_number"}, pytest.raises(ValidationError), None),
        # ошибка в ext_api_request
        (
            None,
            pytest.raises(ExternalAPIHTTPError),
            ExternalAPIHTTPError(status_code=500, detail="Server error"),
        ),
    ],
    ids=[
        "Missing key 'result'",
        "Validation error in data from external API",
        "Error during request to external API",
    ],
)
def test_ext_api_get_exchange_error_cases(
    mocker: MockerFixture, mock_response_data, expectation, side_effect
):
    currency_req = CurrencyRequest(
        currency_1="USD", currency_2="EUR", amount=100
    )
    mocked = mocker.patch("app.api.utils.external_api.ext_api_request")
    if side_effect:
        mocked.side_effect = side_effect
    else:
        mocked.return_value = mock_response_data
    with expectation as e:
        ext_api_get_exchange(currency_req)
    if not side_effect:
        assert "result" in str(e.value)
    else:
        assert e.value == side_effect
