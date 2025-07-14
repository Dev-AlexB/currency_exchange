from typing import Optional

from pydantic import EmailStr


class CustomException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class UniqueFieldException(CustomException):
    MESSAGE_TEMPLATES = {
        "username": "Имя пользователя '{value}' уже используется",
        "email": "Email '{value}' уже используется",
    }

    def __init__(self, field: str, value: str | EmailStr):
        self.field = field
        self.value = value
        self.detail = self._make_message()
        super().__init__(str(self._make_message()))

    def _make_message(self) -> str:
        messages = {
            "username": f"Имя пользователя '{self.value}' уже используется",
            "email": f"Email '{self.value}' уже используется",
        }
        base_message = (
            f"Поле '{self.field}' со значением '{self.value}'"
            f" уже используется"
        )
        return messages.get(self.field, base_message)


class AuthorizationException(CustomException):
    headers = {"WWW-Authenticate": "Bearer"}


class UserUnauthorisedException(AuthorizationException):
    def __init__(self):
        super().__init__("Неверные учетные данные!")


class InvalidTokenException(AuthorizationException):
    def __init__(self, detail: str):
        super().__init__(detail)


class ExternalAPIHTTPError(CustomException):
    def __init__(self, detail: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(detail)


class ExternalAPIDataError(CustomException):
    def __init__(self, key, data_dict):
        self.key = key
        self.data_dict = data_dict
        self.detail = (
            f"Ключ '{key}' не найден в JSON из внешнего API.\n"
            f"Ответ внешнего API: {data_dict}"
        )
        super().__init__(self.detail)
