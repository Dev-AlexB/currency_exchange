from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.db.database import add_user_to_db
from app.api.schemas.users import User, Token, UserCreate
from app.core.security import create_jwt_token, authenticate_user

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)


@auth_router.post('/register/')
async def reg(user: UserCreate) -> dict:
    user = add_user_to_db(user)
    return {
        'message': f'Пользователь {user.username} успешно создан.',
        'details': user,
    }


@auth_router.post('/login/')
async def login(
        form_data: Annotated[User, Depends(OAuth2PasswordRequestForm)]
) -> Token:
    authenticate_user(form_data.username, form_data.password)
    token = create_jwt_token({'sub': form_data.username})
    return Token(access_token=token)

