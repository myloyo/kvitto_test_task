from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import PaymentMethod, PaymentStatus


@dataclass
class Tariff:
    id: str
    title: str
    price: int  # копейки, не рубли и не float


@dataclass
class Payment:
    tariff_id: str
    amount: int
    discount: int
    method: PaymentMethod
    email: str
    status: PaymentStatus = PaymentStatus.pending
    installment_months: int | None = None
    schedule: list[int] | None = None
    idempotency_key: str | None = None
    id: int | None = None
    created_at: datetime | None = None
