from contextlib import nullcontext as does_not_raise

import pytest
from pydantic import ValidationError

from app.api.schemas.currency import (
    CurrencyAll,
    CurrencyRequest,
    CurrencyResponse,
)
from app.api.schemas.users import (
    Token,
    UserBase,
    UserCreate,
    validate_password,
)


class TestUserSchemas:
    def test_validate_password_ok(self):
        value = "PassIsOK5!"
        assert validate_password(value) == value

    @pytest.mark.parametrize(
        "value, message",
        [
            (
                "willfail8&",
                "Пароль должен содержать заглавную букву",
            ),
            (
                "WILLFAIL8&",
                "Пароль должен содержать строчную букву",
            ),
            (
                "Willfail&",
                "Пароль должен содержать цифру",
            ),
            (
                "Willfail8",
                "Пароль должен содержать символ из набора !@$%*?&",
            ),
            (
                "Willfail8&_",
                "Пароль не должен содержать недопустимые символы",
            ),
        ],
        ids=[
            "No uppercase",
            "No lowercase",
            "No digit",
            "No special symbol",
            "Forbidden symbol",
        ],
    )
    def test_validate_password_fail(self, value, message):
        with pytest.raises(ValueError) as exc_info:
            validate_password(value)
        assert message in str(exc_info.value)

    @pytest.mark.parametrize(
        "data, name, email, expectation",
        [
            # нормальные данные и нормализация
            (
                {"username": "Alex", "email": "Alex@example.com"},
                "alex",
                "alex@example.com",
                does_not_raise(),
            ),
            # лишние поля
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "redundant": "something",
                },
                "alex",
                "alex@example.com",
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"username": "bob"},
                None,
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (поле email)
            (
                {"username": "bob", "email": "AAAAAAAAAA"},
                None,
                None,
                pytest.raises(ValidationError),
            ),
        ],
        ids=[
            "Normal data and normalization",
            "Redundant field",
            "Error: not enough fields",
            "Error: wrong email",
        ],
    )
    def test_user_base(self, data, name, email, expectation):
        with expectation as exc_info:
            user = UserBase(**data)
        if exc_info is not None:
            assert any(
                error["loc"] == ("email",) for error in exc_info.value.errors()
            )
        else:
            assert user.username == name
            assert user.email == email

    @pytest.mark.parametrize(
        "data, password, expectation",
        [
            # нормальные данные и нормализация
            (
                {
                    "username": "Alex",
                    "email": "Alex@example.com",
                    "password": "PassIsOK5!",
                },
                "PassIsOK5!",
                does_not_raise(),
            ),
            # лишние поля
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "password": "PassIsOK5!",
                    "redundant": "something",
                },
                "PassIsOK5!",
                does_not_raise(),
            ),
            # ошибка валидации (password отсутствует)
            (
                {"username": "alex", "email": "alex@example.com"},
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (password не соответствует)
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "password": "will_fail",
                },
                None,
                pytest.raises(ValidationError),
            ),
        ],
        ids=[
            "Normal data",
            "Redundant field",
            "Error: not enough fields",
            "Error: unacceptable password",
        ],
    )
    def test_user_create(self, data, password, expectation):
        with expectation as exc_info:
            user = UserCreate(**data)
        if exc_info is not None:
            assert any(
                error["loc"] == ("password",)
                for error in exc_info.value.errors()
            )
        else:
            assert user.password == password

    @pytest.mark.parametrize(
        "data, access_token, token_type, expectation",
        [
            # нормальные данные и проверка поля по умолчанию
            (
                {"access_token": "token"},
                "token",
                "bearer",
                does_not_raise(),
            ),
            # лишние поля
            (
                {
                    "access_token": "token",
                    "token_type": "some_token_type",
                    "redundant": "something",
                },
                "token",
                "some_token_type",
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"token_type": "some_token_type"},
                None,
                None,
                pytest.raises(ValidationError),
            ),
        ],
        ids=[
            "Normal data with blank default field",
            "Redundant field",
            "Error: not enough fields",
        ],
    )
    def test_token(self, data, access_token, token_type, expectation):
        with expectation:
            token = Token(**data)
            assert token.access_token == access_token
            assert token.token_type == token_type


class TestCurrencySchemas:
    @pytest.mark.parametrize(
        "data, expectation, error_location",
        [
            # нормальные данные
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 12.5},
                does_not_raise(),
                None,
            ),
            # лишнее поле и дефолтное поле
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "redundant": "something",
                },
                does_not_raise(),
                None,
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"currency_1": "USD"},
                pytest.raises(ValidationError),
                "to",
            ),
            # ошибка валидации (формат currency)
            (
                {"currency_1": "dollar", "currency_2": "EUR", "amount": 12.5},
                pytest.raises(ValidationError),
                "currency_1",
            ),
            # ошибка валидации (формат amount)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": "one"},
                pytest.raises(ValidationError),
                "amount",
            ),
            # ошибка валидации (значение amount)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 0},
                pytest.raises(ValidationError),
                "amount",
            ),
        ],
        ids=[
            "Normal data",
            "Redundant field and default amount",
            "Error: not enough fields",
            "Error: wrong currency format",
            "Error: amount format not float",
            "Error: amount = 0",
        ],
    )
    def test_currency_request(self, data, expectation, error_location):
        with expectation as exc_info:
            currency_obj = CurrencyRequest(**data)
        if exc_info is not None:
            assert any(
                error["loc"] == (error_location,)
                for error in exc_info.value.errors()
            )
        else:
            assert currency_obj.currency_1 == data["currency_1"]
            assert currency_obj.currency_2 == data["currency_2"]
            assert currency_obj.amount == data.get("amount", 1)

    @pytest.mark.parametrize(
        "data, expectation",
        [
            # нормальные данные
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "amount": 12.5,
                    "result": 10,
                },
                does_not_raise(),
            ),
            # лишнее поле и дефолтное значение
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "result": 1.1,
                    "redundant": "something",
                },
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 12.5},
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (формат result)
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "amount": 12.5,
                    "result": "one",
                },
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (значение result)
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "amount": 12.5,
                    "result": 0,
                },
                pytest.raises(ValidationError),
            ),
        ],
        ids=[
            "Normal data",
            "Redundant field and default amount",
            "Error: not enough fields",
            "Error: result format not float",
            "Error: result = 0",
        ],
    )
    def test_currency_response(self, data, expectation):
        with expectation as exc_info:
            currency_obj = CurrencyResponse(**data)
        if exc_info is not None:
            assert any(
                error["loc"] == ("result",)
                for error in exc_info.value.errors()
            )
        else:
            assert currency_obj.result == data["result"]

    @pytest.mark.parametrize(
        "data, expectation",
        [
            # нормальные данные
            (
                {"currencies": {"USD": "US dollar", "EUR": "euro"}},
                does_not_raise(),
            ),
            # лишнее поле
            (
                {
                    "currencies": {"USD": "US dollar", "EUR": "euro"},
                    "redundant": "something",
                },
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {},
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (currencies не словарь)
            (
                {"currencies": ["USD", "EUR"]},
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (значение по ключу currencies не в том формате)
            (
                {"currencies": {"dollar": "US dollar", "EUR": "euro"}},
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (словарь currencies пуст)
            (
                {"currencies": {}},
                pytest.raises(ValidationError),
            ),
        ],
        ids=[
            "Normal data",
            "Redundant field",
            "Error: not enough fields",
            "Error: currencies format not dict",
            "Error: currencies key wrong format",
            "Error: currencies dict is empty",
        ],
    )
    def test_currency_all(self, data, expectation):
        with expectation as exc_info:
            currency_list_obj = CurrencyAll(**data)
        if exc_info is not None:
            assert any(
                "currencies" in error["loc"]
                for error in exc_info.value.errors()
            )
        else:
            assert currency_list_obj.currencies == data["currencies"]


# тест для проверки работы model_dump у всех схем
@pytest.mark.parametrize(
    "data, schema",
    [
        (
            {"username": "bob", "email": "bob@example.com"},
            UserBase,
        ),
        (
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "ValidPass!8",
            },
            UserCreate,
        ),
        (
            {"access_token": "some_token", "token_type": "bearer"},
            Token,
        ),
        (
            {"currency_1": "USD", "currency_2": "EUR", "amount": 12.5},
            CurrencyRequest,
        ),
        (
            {
                "currency_1": "USD",
                "currency_2": "EUR",
                "amount": 12.5,
                "result": 10,
            },
            CurrencyResponse,
        ),
        (
            {"currencies": {"USD": "US dollar", "EUR": "euro"}},
            CurrencyAll,
        ),
    ],
    ids=[
        "User",
        "UserCreate",
        "Token",
        "CurrencyRequest",
        "CurrencyResponse",
        "CurrencyAll",
    ],
)
def test_schema_to_dict(data, schema):
    schema_obj = schema(**data)
    assert schema_obj.model_dump() == data
