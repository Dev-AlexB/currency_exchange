import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pytest_mock import MockerFixture

from app.api.errors.exceptions import ExternalAPIHTTPError
from app.core.config import settings
from app.core.security import get_username_from_token
from main import app


@pytest_asyncio.fixture
async def async_client(mocker, async_session):
    mocker.patch(
        "app.api.db.UoW.async_session_maker", return_value=async_session
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="class")
def token_check():
    app.dependency_overrides[get_username_from_token] = lambda: "valid_user"
    yield
    app.dependency_overrides = {}


# набор тестов маршрутов авторизации и регистрации
@pytest.mark.usefixtures("setup_test_db")
class TestUsers:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_data, expected_status, expected_message",
        [
            (
                {
                    "username": "new_user",
                    "email": "new@example.com",
                    "password": "ThisPassIsOK8&",
                },
                201,
                "Пользователь new_user успешно создан.",
            ),
            (
                {
                    "username": "existing_user",
                    "email": "new@example.com",
                    "password": "ThisPassIsOK8&",
                },
                400,
                "Имя пользователя 'existing_user' уже используется",
            ),
            (
                {
                    "username": "new_user",
                    "email": "existing@example.com",
                    "password": "ThisPassIsOK8&",
                },
                400,
                "Email 'existing@example.com' уже используется",
            ),
            (
                {"username": "new_user", "password": "ThisPassIsOK8&"},
                422,
                "Ошибка валидации данных клиента.",
            ),
        ],
        ids=[
            "Successful registration",
            "Username already exists",
            "Email already exists",
            "Validation error",
        ],
    )
    async def test_reg(
        self, async_client, input_data, expected_status, expected_message
    ):
        response = await async_client.post("/auth/register/", json=input_data)
        assert response.status_code == expected_status
        assert response.json()["message"] == expected_message

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_data, expected_status, expected_message_or_username",
        [
            (
                {"username": "existing_user", "password": "Password1!"},
                200,
                "existing_user",
            ),
            (
                {"username": "existing_user", "password": "InvalidPassword1!"},
                401,
                "Неверные учетные данные!",
            ),
            (
                {
                    "username": "existing_user",
                },
                422,
                "Ошибка валидации данных клиента.",
            ),
        ],
        ids=["Successful login", "Authentication failure", "Validation error"],
    )
    async def test_login(
        self,
        async_client,
        input_data,
        expected_status,
        expected_message_or_username,
    ):
        response = await async_client.post(
            "/auth/login/",
            data=input_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == expected_status
        if "access_token" in response.json():
            token = response.json()["access_token"]
            payload = jwt.decode(
                token,
                settings.JWT.SECRET_KEY,
                algorithms=[settings.JWT.ALGORITHM],
            )
            assert payload.get("sub") == expected_message_or_username
        else:
            assert response.json()["message"] == expected_message_or_username


# набор тестов маршрутов обмена валюты и списка валют
@pytest.mark.usefixtures("token_check")
class TestCurrency:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query_string, mock_return, mock_side_effect, "
        "expected_status, expected_data",
        [
            # успешный запрос
            (
                "?from=USD&to=EUR",
                {"result": 0.9},
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
                {"result": 8.1},
                None,
                200,
                {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 10,
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
            # ошибка обработки данных из внешнего API (ключ result отсутствует)
            (
                "?from=USD&to=EUR",
                {"outcome": 0.9},
                None,
                500,
                "Проблема с ответом внешнего API",
            ),
            # ошибка валидации (не все поля переданы)
            (
                "?from=USD",
                None,
                None,
                422,
                "Ошибка валидации данных клиента.",
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
    async def test_currency_exchange(
        self,
        mocker: MockerFixture,
        async_client,
        query_string,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_data,
    ):
        mocker.patch(
            "app.api.utils.external_api.ext_api_request",
            new_callable=mocker.AsyncMock,
            return_value=mock_return,
            side_effect=mock_side_effect,
        )
        response = await async_client.get(f"/currency/exchange/{query_string}")
        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json() == expected_data
        else:
            assert response.json()["message"] == expected_data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mock_return, mock_side_effect, expected_status, expected_data",
        [
            # успешный запрос
            (
                {"currencies": {"USD": "US dollar", "EUR": "euro"}},
                None,
                200,
                {"currencies": {"USD": "US dollar", "EUR": "euro"}},
            ),
            # ошибка внешнего API
            (
                None,
                ExternalAPIHTTPError(status_code=404, detail="Uh-oh"),
                500,
                {"message": "Проблема с ответом внешнего API"},
            ),
            # ошибка обработки данных из внешнего API
            (
                {"USD": "US dollar", "EUR": "euro"},
                None,
                500,
                {"message": "Проблема с ответом внешнего API"},
            ),
            # ошибка валидации
            (
                {"currencies": {}},
                None,
                500,
                {"message": "Проблема с ответом внешнего API"},
            ),
        ],
        ids=[
            "Successful response",
            "External API error",
            "External API data processing error",
            "Validation error",
        ],
    )
    async def test_currency_list(
        self,
        mocker: MockerFixture,
        async_client,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_data,
    ):
        mocker.patch(
            "app.api.utils.external_api.ext_api_request",
            new_callable=mocker.AsyncMock,
            return_value=mock_return,
            side_effect=mock_side_effect,
        )
        response = await async_client.get("/currency/list/")
        assert response.status_code == expected_status
        assert response.json() == expected_data
