from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.pricing import is_known_promo


class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    price: int


class PaymentCreate(BaseModel):
    tariff_id: str
    email: EmailStr
    method: PaymentMethod
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @field_validator("promo_code")
    @classmethod
    def _validate_promo(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        if not is_known_promo(value):
            raise ValueError("unknown promo code")
        return value

    @model_validator(mode="after")
    def _validate_installment(self) -> "PaymentCreate":
        if self.method == PaymentMethod.installment and self.installment_months is None:
            raise ValueError("installment_months is required for installment method")
        if self.method != PaymentMethod.installment and self.installment_months is not None:
            raise ValueError("installment_months is allowed only for installment method")
        return self


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: PaymentStatus
    tariff_id: str
    amount: int
    discount: int
    method: PaymentMethod
    installment_months: int | None
    schedule: list[int] | None
    email: str
    created_at: datetime


class WebhookIn(BaseModel):
    payment_id: int
    status: PaymentStatus


class WebhookOut(BaseModel):
    result: Literal["ok"] = "ok"
