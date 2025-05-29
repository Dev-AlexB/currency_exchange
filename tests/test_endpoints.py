import pytest


# набор тестов машрутов авторизации и регистрации
class TestUsers:
    # @pytest.mark.skip
    @pytest.mark.parametrize(
        "data, s_code, message",
        [
            # успешная регистрация и проверка lower
            (
                {
                    "username": "Alex",
                    "email": "alex@example.com",
                    "password": "my_pass",
                },
                201,
                "Пользователь alex успешно создан.",
            ),
            # пользователь уже зарегистрирован
            (
                {
                    "username": "admin",
                    "password": "pass",
                    "email": "admin@mail.ru",
                },
                400,
                "Ошибка 400 - Имя пользователя admin занято. "
                "Пожалуйста, используйте другое!",
            ),
            # не все поля заполнены (проверка валидации)
            (
                {"username": "John"},
                422,
                "Ошибка валидации отправленных данных.",
            ),
        ],
        ids=[
            "Successful registration",
            "Error: username exists",
            "Error: not enough fields",
        ],
    )
    def test_reg(self, data, s_code, message, client):
        response = client.post("/auth/register/", json=data)
        assert response.status_code == s_code
        assert response.json().get("message") == message
