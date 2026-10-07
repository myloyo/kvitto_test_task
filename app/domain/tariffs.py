# 9 900 ₽ = 990_000 копеек. В API и в базе всегда целые копейки.
DEFAULT_TARIFFS: list[dict[str, str | int]] = [
    {"id": "basic", "title": "Basic", "price": 990_000},
    {"id": "standard", "title": "Standard", "price": 1_990_000},
    {"id": "premium", "title": "Premium", "price": 2_990_000},
]
