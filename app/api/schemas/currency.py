from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


ThreeLetterUppercase = Annotated[
    str, StringConstraints(to_upper=True, pattern=r"^[A-Z]{3}$")
]


class CurrencyRequest(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    currency_1: Annotated[ThreeLetterUppercase, Field(..., alias="from")]
    currency_2: Annotated[ThreeLetterUppercase, Field(..., alias="to")]
    amount: Annotated[float, Field(gt=0, default=1)]


class CurrencyResponse(CurrencyRequest):
    result: Annotated[float, Field(gt=0)]


class CurrencyList(BaseModel):
    currencies: dict[ThreeLetterUppercase, str]
