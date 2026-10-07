from app.application.interfaces import PaymentRepository, TariffRepository
from app.domain.entities import Payment, Tariff
from app.domain.enums import PaymentMethod, PaymentStatus, can_transition
from app.domain.exceptions import (
    DuplicateIdempotencyKey,
    InvalidTransition,
    PaymentNotFound,
    TariffNotFound,
)
from app.domain.pricing import apply_discount, build_schedule, discount_percent


def list_tariffs(tariffs: TariffRepository) -> list[Tariff]:
    return tariffs.list_all()


def create_payment(
    tariffs: TariffRepository,
    payments: PaymentRepository,
    *,
    tariff_id: str,
    email: str,
    method: PaymentMethod,
    installment_months: int | None,
    promo_code: str | None,
    idempotency_key: str | None,
) -> tuple[Payment, bool]:
    """Создаёт платёж. Второй элемент — True, если строка новая.

    Тот же Idempotency-Key → возвращаем уже созданный платёж, вторую строку не пишем.
    """
    if idempotency_key:
        existing = payments.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing, False

    tariff = tariffs.get(tariff_id)
    if tariff is None:
        raise TariffNotFound(tariff_id)

    percent = discount_percent(promo_code)
    amount, discount = apply_discount(tariff.price, percent)

    schedule: list[int] | None = None
    if method == PaymentMethod.installment:
        if installment_months is None:
            raise ValueError("для рассрочки нужен installment_months")
        schedule = build_schedule(amount, installment_months)

    payment = Payment(
        tariff_id=tariff.id,
        amount=amount,
        discount=discount,
        method=method,
        email=email,
        installment_months=installment_months,
        schedule=schedule,
        idempotency_key=idempotency_key,
    )
    try:
        saved = payments.add(payment)
    except DuplicateIdempotencyKey:
        # Два одинаковых запроса пришли одновременно: победил первый commit.
        if idempotency_key:
            existing = payments.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing, False
        raise
    return saved, True


def get_payment(payments: PaymentRepository, payment_id: int) -> Payment:
    payment = payments.get(payment_id)
    if payment is None:
        raise PaymentNotFound(payment_id)
    return payment


def list_payments(
    payments: PaymentRepository,
    *,
    email: str | None = None,
    status: PaymentStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Payment]:
    return payments.list_filtered(email=email, status=status, limit=limit, offset=offset)


def apply_status_change(
    payments: PaymentRepository,
    payment_id: int,
    new_status: PaymentStatus,
) -> Payment:
    payment = get_payment(payments, payment_id)
    if not can_transition(payment.status, new_status):
        raise InvalidTransition(f"{payment.status.value} -> {new_status.value}")
    payment.status = new_status
    return payments.save(payment)
