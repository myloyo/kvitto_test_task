import hashlib
import hmac


def compute_signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = compute_signature(secret, body)
    # compare_digest — чтобы по времени ответа нельзя было подобрать подпись.
    return hmac.compare_digest(expected, signature)
