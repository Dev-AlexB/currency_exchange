from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.schemas.currency import (
    CurrencyList,
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
    currency_1: Annotated[str, Query(..., alias="from")],
    currency_2: Annotated[str, Query(..., alias="to")],
    amount: int,
) -> CurrencyResponse:
    params = locals()
    return ext_api_get_exchange(CurrencyRequest(**params))


@currency_router.get("/list/")
async def currency_list() -> CurrencyList:
    return ext_api_get_currencies()
