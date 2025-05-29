from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


ThreeLetterUppercase = Annotated[
    str, StringConstraints(to_upper=True, pattern=r"^[A-Z]{3}$")
]


class CurrencyRequest(BaseModel):
    # model_config = ConfigDict(populate_by_name=True)

    currency_1: ThreeLetterUppercase
    currency_2: ThreeLetterUppercase
    amount: float = Field(gt=0, default=1)


class CurrencyResponse(CurrencyRequest):
    result: float = Field(gt=0)


class CurrencyList(BaseModel):
    currencies: dict[ThreeLetterUppercase, str]
