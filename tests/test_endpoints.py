import pytest
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pytest_mock import MockerFixture

from app.api.errors.exceptions import (
    ExternalAPIHTTPError,
    ExternalAPIKeyError,
    InvalidUsernameException,
    UserUnauthorisedException,
)
from app.api.schemas.currency import CurrencyList, CurrencyResponse
from app.api.schemas.users import User, UserCreate, UserInDB
from app.core.security import get_username_from_token
from main import app


# набор тестов маршрутов авторизации и регистрации
class TestUsers:
    @pytest.mark.parametrize(
        "input_data, mock_return, mock_side_effect, "
        "expected_status, expected_message, expected_username",
        [
            # Успешная регистрация
            (
                {
                    "username": "valid_name",
                    "email": "valid@email.com",
                    "password": "valid_pass",
                },
                User(username="valid_name", email="valid@email.com"),
                None,
                201,
                "Пользователь valid_name успешно создан.",
                "valid_name",
            ),
            # Пользователь уже существует
            (
                {
                    "username": "admin",
                    "email": "admin@mail.ru",
                    "password": "pass",
                },
                None,
                InvalidUsernameException("admin"),
                400,
                "Имя пользователя admin занято.",
                None,
            ),
            # Ошибка валидации (не хватает полей)
            (
                {"username": "valid_name"},
                None,
                RequestValidationError(
                    errors=[
                        "some error",
                    ]
                ),
                422,
                "Ошибка валидации отправленных клиентом данных.",
                None,
            ),
        ],
        ids=[
            "Successful registration",
            "Username already exists",
            "Validation error",
        ],
    )
    def test_reg(
        self,
        mocker: MockerFixture,
        client,
        input_data,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_message,
        expected_username,
    ):
        mock = mocker.patch(
            "app.api.db.services.UserService.register_user",
            return_value=mock_return,
            side_effect=mock_side_effect,
        )
        response = client.post("/auth/register", json=input_data)
        assert response.status_code == expected_status
        assert expected_message in response.json()["message"]
        if expected_username:
            assert response.json()["details"]["username"] == expected_username
            mock.assert_called_once_with(UserCreate(**input_data))

    @pytest.mark.parametrize(
        "input_data, mock_return_user, mock_side_effect, mock_return_token, "
        "expected_status, expected_data",
        [
            # успешное получение токена
            (
                {"username": "valid_user", "password": "valid_pass"},
                UserInDB(
                    username="valid_user",
                    email="valid@email.com",
                    hashed_password="valid_pass",
                ),
                None,
                "valid_token",
                200,
                {"access_token": "valid_token", "token_type": "bearer"},
            ),
            # провал аутентификации
            (
                {"username": "valid_user", "password": "invalid_pass"},
                None,
                UserUnauthorisedException(),
                None,
                401,
                {"message": "Ошибка 401 - Неверные учетные данные!"},
            ),
            # ошибка валидации (не все поля переданы)
            (
                {"username": "valid_user"},
                None,
                None,
                None,
                422,
                None,
            ),
        ],
        ids=["Successful login", "Authentication failure", "Validation error"],
    )
    def test_login(
        self,
        mocker: MockerFixture,
        client,
        input_data,
        mock_return_user,
        mock_side_effect,
        mock_return_token,
        expected_status,
        expected_data,
    ):
        mock_authenticate_user = mocker.patch(
            "app.api.db.services.UserService.authenticate_user",
            return_value=mock_return_user,
            side_effect=mock_side_effect,
        )
        mock_create_jwt_token = mocker.patch(
            "app.api.endpoints.users.create_jwt_token",
            return_value=mock_return_token,
        )
        response = client.post(
            "/auth/login/",
            data=input_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == expected_status
        if expected_data:
            assert response.json() == expected_data
        if "password" in input_data and "username" in input_data:
            mock_authenticate_user.assert_called_once_with(
                input_data["username"], input_data["password"]
            )
        else:
            mock_authenticate_user.assert_not_called()
        if mock_return_token:
            mock_create_jwt_token.assert_called_once_with(
                {"sub": mock_return_user.username}
            )
        else:
            mock_create_jwt_token.assert_not_called()


# набор тестов маршрутов обмена валюты и списка валют
class TestCurrency:
    @pytest.mark.parametrize(
        "query_string, mock_return, mock_side_effect, "
        "expected_status, expected_data",
        [
            # успешный запрос
            (
                "?from=USD&to=EUR",
                CurrencyResponse(
                    currency_1="USD", currency_2="EUR", amount=1, result=0.9
                ),
                None,
                200,
                {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 1,
                    "result": 0.9,
                },
            ),
            # лишнее поле
            (
                "?from=USD&to=EUR&amount=10&field=something",
                CurrencyResponse(
                    currency_1="USD",
                    currency_2="EUR",
                    amount=9,
                    result=8.1,
                ),
                None,
                200,
                {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 9,
                    "result": 8.1,
                },
            ),
            # ошибка внешнего API
            (
                "?from=AAA&to=BBB",
                None,
                ExternalAPIHTTPError(status_code=402, detail="Uh-oh"),
                400,
                "Код валюты не найден. Для проверки доступных "
                "кодов воспользуйтесь URL currency/list",
            ),
            # ошибка обработки данных из внешнего API
            (
                "?from=USD&to=EUR",
                None,
                ExternalAPIKeyError(key="result", data_dict={"outcome": 0.9}),
                500,
                "Проблема с ответом внешнего API",
            ),
            # ошибка валидации (не все поля переданы)
            (
                "?from=USD",
                None,
                None,
                422,
                "Ошибка валидации отправленных клиентом данных.",
            ),
        ],
        ids=[
            "Successful response",
            "Redundant field",
            "External API error",
            "External API data processing error",
            "Validation error",
        ],
    )
    def test_currency_exchange(
        self,
        mocker: MockerFixture,
        client,
        query_string,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_data,
    ):
        app.dependency_overrides[get_username_from_token] = (
            lambda: "valid_user"
        )

        mocker.patch(
            "app.api.endpoints.currency.ext_api_get_exchange",
            return_value=mock_return,
            side_effect=mock_side_effect,
            autospec=True,
        )
        response = client.get(f"/currency/exchange/{query_string}")
        assert response.status_code == expected_status
        if mock_return:
            assert response.json() == expected_data
        else:
            assert response.json()["message"] == expected_data
        app.dependency_overrides = {}

    @pytest.mark.problem
    @pytest.mark.parametrize(
        "mock_return, mock_side_effect, expected_status, expected_data",
        [
            # успешный запрос
            (
                CurrencyList(currencies={"USD": "US dollar", "EUR": "euro"}),
                None,
                200,
                {"currencies": {"USD": "US dollar", "EUR": "euro"}},
            ),
            # ошибка внешнего API
            (
                None,
                ExternalAPIHTTPError(status_code=402, detail="text"),
                400,
                {
                    "message": "Код валюты не найден. "
                    "Для проверки доступных кодов "
                    "воспользуйтесь URL currency/list"
                },
            ),
            # ошибка обработки данных из внешнего API
            (
                None,
                ExternalAPIKeyError(
                    key="currencies",
                    data_dict={"USD": "US dollar", "EUR": "euro"},
                ),
                500,
                {"message": "Проблема с ответом внешнего API"},
            ),
            # ошибка валидации
            (
                None,
                ResponseValidationError(errors=["some_error"]),
                500,
                {"message": "Внутренняя ошибка сервера."},
            ),
        ],
        ids=[
            "Successful response",
            "External API error",
            "External API data processing error",
            "Validation error",
        ],
    )
    def test_currency_list(
        self,
        mocker: MockerFixture,
        client,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_data,
    ):
        app.dependency_overrides[get_username_from_token] = (
            lambda: "valid_user"
        )
        mocker.patch(
            "app.api.endpoints.currency.ext_api_get_currencies",
            return_value=mock_return,
            side_effect=mock_side_effect,
        )
        response = client.get("/currency/list/")
        assert response.status_code == expected_status
        assert response.json() == expected_data
        app.dependency_overrides = {}
