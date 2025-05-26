from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.db.services import UserService, get_user_service
from app.api.schemas.users import Token, User, UserCreate
from app.core.security import create_jwt_token


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post("/register/")
async def reg(
    user: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    user = user_service.register_user(user)
    return {
        "message": f"Пользователь {user.username} успешно создан.",
        "details": user,
    }


@auth_router.post("/login/")
async def login(
    form_data: Annotated[User, Depends(OAuth2PasswordRequestForm)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    user_service.authenticate_user(form_data.username, form_data.password)
    token = create_jwt_token({"sub": form_data.username})
    return Token(access_token=token)
