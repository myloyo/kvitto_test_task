import pytest


def _create_payment(client, **overrides) -> dict:
    payload = {
        "tariff_id": "standard",
        "email": "student@example.com",
        "method": "card",
        **overrides,
    }
    response = client.post("/payments", json=payload)
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_amount_with_and_without_promo_including_lowercase(client):
    without_promo = _create_payment(client, email="no-promo@example.com")
    assert without_promo["amount"] == 1_990_000
    assert without_promo["discount"] == 0

    with_promo = _create_payment(
        client,
        email="promo@example.com",
        promo_code="kvitto10",
    )
    assert with_promo["amount"] == 1_791_000
    assert with_promo["discount"] == 199_000

    unknown = client.post(
        "/payments",
        json={
            "tariff_id": "standard",
            "email": "bad-promo@example.com",
            "method": "card",
            "promo_code": "UNKNOWN",
        },
    )
    assert unknown.status_code == 422


@pytest.mark.parametrize("months", [3, 6, 12])
def test_installment_schedule_sums_to_amount(client, months: int):
    payment = _create_payment(
        client,
        email=f"inst-{months}@example.com",
        method="installment",
        installment_months=months,
    )
    schedule = payment["schedule"]
    assert schedule is not None
    assert len(schedule) == months
    assert sum(schedule) == payment["amount"]
    assert payment["amount"] == 1_990_000

    if months == 3:
        assert schedule == [663_334, 663_333, 663_333]


def test_same_idempotency_key_does_not_create_second_payment(client):
    payload = {
        "tariff_id": "basic",
        "email": "idem@example.com",
        "method": "sbp",
    }
    headers = {"Idempotency-Key": "pay-1"}

    first = client.post("/payments", json=payload, headers=headers)
    second = client.post("/payments", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    listed = client.get("/payments", params={"email": "idem@example.com"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_forbidden_status_transition_returns_409_and_keeps_status(client):
    payment = _create_payment(client, email="status@example.com")
    payment_id = payment["id"]

    ok = client.post(
        "/webhooks/bank",
        json={"payment_id": payment_id, "status": "succeeded"},
    )
    assert ok.status_code == 200
    assert ok.json() == {"result": "ok"}

    forbidden = client.post(
        "/webhooks/bank",
        json={"payment_id": payment_id, "status": "failed"},
    )
    assert forbidden.status_code == 409
    assert forbidden.json() == {"error": "invalid_transition"}

    current = client.get(f"/payments/{payment_id}")
    assert current.status_code == 200
    assert current.json()["status"] == "succeeded"


def test_missing_payment_returns_404(client):
    response = client.get("/payments/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "payment not found"

    webhook = client.post(
        "/webhooks/bank",
        json={"payment_id": 999999, "status": "succeeded"},
    )
    assert webhook.status_code == 404
