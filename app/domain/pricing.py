from app.domain.exceptions import UnknownPromoCode

PROMO_CODES: dict[str, int] = {
    "KVITTO10": 10,  # скидка в процентах; в коде буква O, не ноль
}


def normalize_promo(code: str | None) -> str | None:
    if code is None:
        return None
    code = code.strip().upper()
    return code or None


def is_known_promo(code: str) -> bool:
    return normalize_promo(code) in PROMO_CODES


def discount_percent(promo_code: str | None) -> int:
    code = normalize_promo(promo_code)
    if code is None:
        return 0
    if code not in PROMO_CODES:
        raise UnknownPromoCode(code)
    return PROMO_CODES[code]


def apply_discount(price: int, percent: int) -> tuple[int, int]:
    """(сумма к оплате, скидка) в копейках. Только целая арифметика.

    >>> apply_discount(1_990_000, 10)
    (1791000, 199000)
    """
    if percent <= 0:
        return price, 0
    discount = price * percent // 100
    return price - discount, discount


def build_schedule(amount: int, months: int) -> list[int]:
    """Делит сумму на месяцы так, чтобы сумма графика была ровно amount.

    Остаток копеек кладём в первые платежи, не в последний.

    >>> build_schedule(1_990_000, 3)
    [663334, 663333, 663333]
    """
    if months <= 0:
        raise ValueError("срок рассрочки должен быть больше нуля")
    base, remainder = divmod(amount, months)
    return [base + 1 if i < remainder else base for i in range(months)]
