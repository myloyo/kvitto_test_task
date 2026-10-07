PAYMENT_FIELDS = {
    "id",
    "status",
    "tariff_id",
    "amount",
    "discount",
    "method",
    "installment_months",
    "schedule",
    "email",
    "created_at",
}


def _create(client, **overrides) -> dict:
    payload = {
        "tariff_id": "standard",
        "email": "student@example.com",
        "method": "card",
        **overrides,
    }
    response = client.post("/payments", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_created_payment_has_required_fields_and_pending_status(client):
    payment = _create(client, email="fields@example.com")
    assert payment["status"] == "pending"
    assert payment["schedule"] is None
    assert payment["installment_months"] is None
    assert set(payment) == PAYMENT_FIELDS

    fetched = client.get(f"/payments/{payment['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == payment["id"]
    assert fetched.json()["email"] == "fields@example.com"


def test_unknown_tariff_returns_404(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": "gold",
            "email": "no-tariff@example.com",
            "method": "card",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "tariff not found"


def test_installment_without_months_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": "standard",
            "email": "no-months@example.com",
            "method": "installment",
        },
    )
    assert response.status_code == 422


def test_months_not_allowed_for_card_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": "standard",
            "email": "card-months@example.com",
            "method": "card",
            "installment_months": 3,
        },
    )
    assert response.status_code == 422


def test_list_payments_filters_by_email_and_status(client):
    pending = _create(client, email="filter@example.com")
    _create(client, email="other@example.com")

    listed = client.get("/payments", params={"email": "filter@example.com"})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [pending["id"]]

    by_status = client.get("/payments", params={"status": "pending", "email": "filter@example.com"})
    assert len(by_status.json()) == 1
    assert by_status.json()[0]["status"] == "pending"
