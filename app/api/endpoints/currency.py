from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.schemas.currency import (
    CurrencyAll,
    CurrencyRequest,
    CurrencyResponse,
)
from app.api.utils.external_api import (
    ext_api_get_currencies,
    ext_api_get_exchange,
)
from app.core.security import get_username_from_token


currency_router = APIRouter(
    prefix="/currency",
    tags=["currency"],
    dependencies=[Depends(get_username_from_token)],
)


@currency_router.get("/exchange/")
async def currency_exchange(
    request: Annotated[CurrencyRequest, Query()],
) -> CurrencyResponse:
    return await ext_api_get_exchange(request)


@currency_router.get("/list/")
async def currency_list() -> CurrencyAll:
    return await ext_api_get_currencies()
