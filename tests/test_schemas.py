from contextlib import nullcontext as does_not_raise

import pytest
from pydantic import ValidationError

from app.api.schemas.currency import (
    CurrencyAll,
    CurrencyRequest,
    CurrencyResponse,
)
from app.api.schemas.users import Token, User, UserCreate, UserInDB


class TestUserSchemas:
    @pytest.mark.parametrize(
        "data, name, email, expectation",
        [
            # нормальные данные
            (
                {"username": "alex", "email": "alex@example.com"},
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
            "Normal data",
            "Redundant field",
            "Error: not enough fields",
            "Error: wrong email",
        ],
    )
    def test_user(self, data, name, email, expectation):
        with expectation:
            user = User(**data)
            assert user.username == name
            assert user.email == email

    @pytest.mark.parametrize(
        "data, password, expectation",
        [
            # нормальные данные
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "password": "my_pass",
                },
                "my_pass",
                does_not_raise(),
            ),
            # лишние поля
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "password": "my_pass",
                    "redundant": "something",
                },
                "my_pass",
                does_not_raise(),
            ),
            # ошибка валидации (password отсутствует)
            (
                {"username": "alex", "email": "alex@example.com"},
                None,
                pytest.raises(ValidationError),
            ),
        ],
        ids=["Normal data", "Redundant field", "Error: not enough fields"],
    )
    def test_user_create(self, data, password, expectation):
        with expectation:
            user = UserCreate(**data)
            assert user.password == password

    @pytest.mark.parametrize(
        "data, hashed_password, expectation",
        [
            # нормальные данные
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "hashed_password": "my_pass",
                },
                "my_pass",
                does_not_raise(),
            ),
            # лишние поля
            (
                {
                    "username": "alex",
                    "email": "alex@example.com",
                    "hashed_password": "my_pass",
                    "redundant": "something",
                },
                "my_pass",
                does_not_raise(),
            ),
            # ошибка валидации (hashed_password отсутствует)
            (
                {"username": "alex", "email": "alex@example.com"},
                None,
                pytest.raises(ValidationError),
            ),
        ],
        ids=["Normal data", "Redundant field", "Error: not enough fields"],
    )
    def test_user_in_db(self, data, hashed_password, expectation):
        with expectation:
            user = UserInDB(**data)
            assert user.hashed_password == hashed_password

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

    def test_user_error_content(self):
        with pytest.raises(ValidationError) as e:
            User(username="Name", email="invalid_email")
        assert any(error["loc"] == ("email",) for error in e.value.errors())


class TestCurrencySchemas:
    @pytest.mark.parametrize(
        "data, currency_1, currency_2, amount, expectation",
        [
            # нормальные данные
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 12.5},
                "USD",
                "EUR",
                12.5,
                does_not_raise(),
            ),
            # лишнее поле и дефолтное поле
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "redundant": "something",
                },
                "USD",
                "EUR",
                1,
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"currency_1": "USD"},
                None,
                None,
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (формат currency)
            (
                {"currency_1": "dollar", "currency_2": "EUR", "amount": 12.5},
                None,
                None,
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (формат amount)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": "one"},
                None,
                None,
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (значение amount)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 0},
                None,
                None,
                None,
                pytest.raises(ValidationError),
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
    def test_currency_request(
        self, data, currency_1, currency_2, amount, expectation
    ):
        with expectation:
            currency_obj = CurrencyRequest(**data)
            assert currency_obj.currency_1 == currency_1
            assert currency_obj.currency_2 == currency_2
            assert currency_obj.amount == amount

    @pytest.mark.parametrize(
        "data, result, expectation",
        [
            # нормальные данные
            (
                {
                    "currency_1": "USD",
                    "currency_2": "EUR",
                    "amount": 12.5,
                    "result": 10,
                },
                10,
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
                1.1,
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {"currency_1": "USD", "currency_2": "EUR", "amount": 12.5},
                None,
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
                None,
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
                None,
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
    def test_currency_response(self, data, result, expectation):
        with expectation:
            currency_obj = CurrencyResponse(**data)
            assert currency_obj.result == result

    @pytest.mark.parametrize(
        "data, currencies, expectation",
        [
            # нормальные данные
            (
                {"currencies": {"USD": "US dollar", "EUR": "euro"}},
                {"USD": "US dollar", "EUR": "euro"},
                does_not_raise(),
            ),
            # лишнее поле
            (
                {
                    "currencies": {"USD": "US dollar", "EUR": "euro"},
                    "redundant": "something",
                },
                {"USD": "US dollar", "EUR": "euro"},
                does_not_raise(),
            ),
            # ошибка валидации (не все поля заполнены)
            (
                {},
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (currencies не словарь)
            (
                {"currencies": ["USD", "EUR"]},
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (значение по ключу currencies не в том формате)
            (
                {"currencies": {"dollar": "US dollar", "EUR": "euro"}},
                None,
                pytest.raises(ValidationError),
            ),
            # ошибка валидации (словарь currencies пуст)
            (
                {"currencies": {}},
                None,
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
    def test_currency_all(self, data, currencies, expectation):
        with expectation:
            currency_list_obj = CurrencyAll(**data)
            assert currency_list_obj.currencies == currencies


# тест для проверки работы model_dump у всех схем
@pytest.mark.parametrize(
    "data, schema",
    [
        (
            {"username": "bob", "email": "bob@example.com"},
            User,
        ),
        (
            {
                "username": "bob",
                "email": "bob@example.com",
                "password": "bob_pass",
            },
            UserCreate,
        ),
        (
            {
                "username": "bob",
                "email": "bob@example.com",
                "hashed_password": "hashed_bob_pass",
            },
            UserInDB,
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
        "UserInDB",
        "Token",
        "CurrencyRequest",
        "CurrencyResponse",
        "CurrencyAll",
    ],
)
def test_schema_to_dict(data, schema):
    schema_obj = schema(**data)
    assert schema_obj.model_dump() == data
