import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

Money = Annotated[int, Field(strict=True, ge=0, le=100_000_000)]
Identifier = Annotated[str, Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_-]+$")]
Method = Literal["Pix", "Débito", "Crédito", "Link de pagamento"]

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class ProductInput(Input):
    id: Identifier
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(default="Alimentos", min_length=1, max_length=60)
    price: Money
    cost: Money
    weight_grams: int | None = Field(default=None, strict=True, ge=1, le=1_000_000)
    active: Literal[0, 1] = 1

class CartItem(Input):
    id: Identifier
    qty: int = Field(strict=True, ge=1, le=999)

class SaleInput(Input):
    id: Identifier
    items: list[CartItem] = Field(min_length=1, max_length=100)
    event: str = Field(default="Varejo que dá resultado", min_length=1, max_length=120)
    status: Literal["pending", "paid"]
    method: Method
    email: str = Field(default="", max_length=254)
    customer: str = Field(default="", max_length=120)
    fee: Money = 0
    automatic_fees: StrictBool = False

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        if value and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Informe um e-mail válido.")
        return value

    @field_validator("items")
    @classmethod
    def unique_items(cls, value):
        if len({i.id for i in value}) != len(value):
            raise ValueError("O mesmo produto não pode aparecer duas vezes.")
        return value

class StatusInput(Input):
    status: Literal["paid", "cancelled"]

class DisplayInput(Input):
    event: str = Field(min_length=1, max_length=120)
    items: list[CartItem] = Field(max_length=100)
    updatedAt: int = Field(strict=True, gt=0)

    @field_validator("items")
    @classmethod
    def unique_items(cls, value):
        if len({i.id for i in value}) != len(value):
            raise ValueError("Produtos duplicados.")
        return value

class LoginInput(Input):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=500)

class EventInput(Input):
    name: str = Field(min_length=1, max_length=120)
