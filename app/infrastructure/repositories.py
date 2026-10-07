from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import Payment, Tariff
from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.exceptions import DuplicateIdempotencyKey
from app.infrastructure.models import PaymentModel, TariffModel


def _tariff_to_domain(row: TariffModel) -> Tariff:
    return Tariff(id=row.id, title=row.title, price=row.price)


def _payment_to_domain(row: PaymentModel) -> Payment:
    return Payment(
        id=row.id,
        status=PaymentStatus(row.status),
        tariff_id=row.tariff_id,
        amount=row.amount,
        discount=row.discount,
        method=PaymentMethod(row.method),
        installment_months=row.installment_months,
        schedule=row.schedule,
        email=row.email,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
    )


class SqlAlchemyTariffRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[Tariff]:
        rows = self._db.scalars(select(TariffModel).order_by(TariffModel.price))
        return [_tariff_to_domain(row) for row in rows]

    def get(self, tariff_id: str) -> Tariff | None:
        row = self._db.get(TariffModel, tariff_id)
        return _tariff_to_domain(row) if row else None


class SqlAlchemyPaymentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, payment_id: int) -> Payment | None:
        row = self._db.get(PaymentModel, payment_id)
        return _payment_to_domain(row) if row else None

    def get_by_idempotency_key(self, key: str) -> Payment | None:
        row = self._db.scalar(select(PaymentModel).where(PaymentModel.idempotency_key == key))
        return _payment_to_domain(row) if row else None

    def add(self, payment: Payment) -> Payment:
        row = PaymentModel(
            status=payment.status.value,
            tariff_id=payment.tariff_id,
            amount=payment.amount,
            discount=payment.discount,
            method=payment.method.value,
            installment_months=payment.installment_months,
            schedule=payment.schedule,
            email=payment.email,
            idempotency_key=payment.idempotency_key,
        )
        self._db.add(row)
        try:
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise DuplicateIdempotencyKey(payment.idempotency_key) from exc
        self._db.refresh(row)
        return _payment_to_domain(row)

    def save(self, payment: Payment) -> Payment:
        if payment.id is None:
            raise ValueError("нельзя сохранить платёж без id")
        row = self._db.get(PaymentModel, payment.id)
        if row is None:
            raise ValueError(f"платёж {payment.id} не найден в базе")
        row.status = payment.status.value
        row.tariff_id = payment.tariff_id
        row.amount = payment.amount
        row.discount = payment.discount
        row.method = payment.method.value
        row.installment_months = payment.installment_months
        row.schedule = payment.schedule
        row.email = payment.email
        row.idempotency_key = payment.idempotency_key
        self._db.commit()
        self._db.refresh(row)
        return _payment_to_domain(row)

    def list_filtered(
        self,
        *,
        email: str | None = None,
        status: PaymentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        stmt = select(PaymentModel).order_by(PaymentModel.id.desc()).limit(limit).offset(offset)
        if email:
            stmt = stmt.where(PaymentModel.email == email)
        if status is not None:
            stmt = stmt.where(PaymentModel.status == status.value)
        return [_payment_to_domain(row) for row in self._db.scalars(stmt)]
