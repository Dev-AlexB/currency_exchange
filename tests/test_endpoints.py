import pytest
from fastapi.exceptions import RequestValidationError

from app.api.errors.exceptions import InvalidUsernameException
from app.api.schemas.users import User


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
                "Ошибка валидации отправленных данных.",
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
        mocker,
        client,
        input_data,
        mock_return,
        mock_side_effect,
        expected_status,
        expected_message,
        expected_username,
    ):
        mocker.patch(
            "app.api.db.services.UserService.register_user",
            return_value=mock_return,
            side_effect=mock_side_effect,
        )
        response = client.post("/auth/register", json=input_data)
        assert response.status_code == expected_status
        assert expected_message in response.json()["message"]
        if expected_username:
            assert response.json()["details"]["username"] == expected_username

    def test_login(self):
        pass
