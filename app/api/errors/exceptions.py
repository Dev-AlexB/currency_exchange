from fastapi import HTTPException, status

class CustomException(HTTPException):
    pass


class InvalidUsernameException(CustomException):
    def __init__(self, name):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Имя пользователя {name} занято. ' 
                   'Пожалуйста, используйте другое!'
        )


class UserUnauthorisedException(CustomException):
    def __init__(self, detail=None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or 'Неверные учетные данные!',
            headers={'WWW-Authenticate': 'Bearer'},
        )


class InvalidTokenException(UserUnauthorisedException):
    pass


class ExternalAPIError(CustomException):
    pass
