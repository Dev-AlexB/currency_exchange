from pydantic import BaseModel, Field, ConfigDict



class CurrencyRequest(BaseModel):
    # model_config = ConfigDict(populate_by_name=True)

    currency_1: str
    currency_2: str
    amount: float  = Field(gt=0, default=1)


class CurrencyResponse(CurrencyRequest):
    result: float


class CurrencyList(BaseModel):
    currencies: dict[str, str]