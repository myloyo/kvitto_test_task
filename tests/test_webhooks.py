import json

from app.infrastructure.config import get_settings
from app.infrastructure.security import compute_signature


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


def test_pending_to_failed_then_keeps_failed(client):
    payment = _create(client, email="fail@example.com")

    ok = client.post(
        "/webhooks/bank",
        json={"payment_id": payment["id"], "status": "failed"},
    )
    assert ok.status_code == 200
    assert ok.json() == {"result": "ok"}

    forbidden = client.post(
        "/webhooks/bank",
        json={"payment_id": payment["id"], "status": "succeeded"},
    )
    assert forbidden.status_code == 409
    assert forbidden.json() == {"error": "invalid_transition"}
    assert client.get(f"/payments/{payment['id']}").json()["status"] == "failed"


def test_succeeded_to_refunded(client):
    payment = _create(client, email="refund@example.com")
    client.post("/webhooks/bank", json={"payment_id": payment["id"], "status": "succeeded"})

    refunded = client.post(
        "/webhooks/bank",
        json={"payment_id": payment["id"], "status": "refunded"},
    )
    assert refunded.status_code == 200
    assert client.get(f"/payments/{payment['id']}").json()["status"] == "refunded"


def test_webhook_missing_payment_returns_404(client):
    response = client.post(
        "/webhooks/bank",
        json={"payment_id": 999999, "status": "succeeded"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "payment not found"


def test_webhook_invalid_json_returns_422(client):
    response = client.post(
        "/webhooks/bank",
        content=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_webhook_signature_required_when_enabled(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "webhook_verify_signature", True)
    monkeypatch.setattr(settings, "webhook_secret", "test-secret")

    payment = _create(client, email="sign@example.com")
    body = json.dumps({"payment_id": payment["id"], "status": "succeeded"}).encode()
    headers = {"Content-Type": "application/json"}

    without_sig = client.post("/webhooks/bank", content=body, headers=headers)
    assert without_sig.status_code == 401

    headers["X-Signature"] = compute_signature("test-secret", body)
    with_sig = client.post("/webhooks/bank", content=body, headers=headers)
    assert with_sig.status_code == 200
    assert with_sig.json() == {"result": "ok"}
