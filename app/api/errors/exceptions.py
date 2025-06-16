from fastapi import HTTPException, status


class InvalidUsernameException(HTTPException):
    def __init__(self, name):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Имя пользователя {name} занято. "
            "Пожалуйста, используйте другое!",
        )


class UserUnauthorisedException(HTTPException):
    def __init__(self, detail=None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "Неверные учетные данные!",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(UserUnauthorisedException):
    pass


class ExternalAPIHTTPError(HTTPException):
    pass


class ExternalAPIKeyError(KeyError):
    def __init__(self, key, data_dict):
        self.message = (
            f"Ключ '{key}' не найден в JSON из внешнего API.\n"
            f"Ответ внешнего API: {data_dict}"
        )
        super().__init__(self.message)
