from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.schemas.users import Token, UserCreate
from app.api.services.user_service import IUserService, get_user_service
from app.core.security import create_jwt_token


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post("/register/", status_code=status.HTTP_201_CREATED)
async def reg(
    user: UserCreate,
    user_service: Annotated[IUserService, Depends(get_user_service)],
) -> dict:
    user = await user_service.register_user(user)
    return {
        "message": f"Пользователь {user.username} успешно создан.",
        "details": user,
    }


@auth_router.post("/login/")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[IUserService, Depends(get_user_service)],
) -> Token:
    username = await user_service.authenticate_user(
        form_data.username, form_data.password
    )
    token = create_jwt_token({"sub": username})
    return Token(access_token=token)
