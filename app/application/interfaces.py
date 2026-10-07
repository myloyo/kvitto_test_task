from typing import Protocol

from app.domain.entities import Payment, Tariff
from app.domain.enums import PaymentStatus


class TariffRepository(Protocol):
    def list_all(self) -> list[Tariff]: ...
    def get(self, tariff_id: str) -> Tariff | None: ...


class PaymentRepository(Protocol):
    def get(self, payment_id: int) -> Payment | None: ...
    def get_by_idempotency_key(self, key: str) -> Payment | None: ...
    def add(self, payment: Payment) -> Payment: ...
    def save(self, payment: Payment) -> Payment: ...
    def list_filtered(
        self,
        *,
        email: str | None = None,
        status: PaymentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]: ...
