"""Runnable minimal example of a safe, idempotent, signature-verified webhook handler.

Personal portfolio project. Uses SQLite in-memory storage and synthetic test payloads.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time


class SafeWebhookReceiver:
    def __init__(self, secret: str, max_age_seconds: int = 300):
        self.secret = secret
        self.max_age_seconds = max_age_seconds
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(
            """
            CREATE TABLE wallets (user_id TEXT PRIMARY KEY, balance_kobo INTEGER NOT NULL);
            CREATE TABLE processed_webhooks (event_id TEXT PRIMARY KEY, processed_at INTEGER NOT NULL);
            """
        )
        self.conn.execute("INSERT INTO wallets VALUES ('USR-101', 0)")
        self.conn.commit()

    def verify_signature(self, raw_body: bytes, timestamp: int, signature: str, now: int) -> None:
        if abs(now - timestamp) > self.max_age_seconds:
            raise PermissionError("Webhook timestamp outside replay tolerance window")
        signed_bytes = f"{timestamp}.".encode("utf-8") + raw_body
        expected = hmac.new(self.secret.encode("utf-8"), signed_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise PermissionError("Invalid HMAC signature")

    def handle(self, raw_body: bytes, timestamp: int, signature: str, now: int | None = None) -> tuple[int, dict]:
        now_ts = int(time.time()) if now is None else now
        self.verify_signature(raw_body, timestamp, signature, now_ts)
        event = json.loads(raw_body.decode("utf-8"))
        event_id = event["event_id"]
        user_id = event["user_id"]
        amount_kobo = int(event["amount_kobo"])

        try:
            with self.conn:
                # Atomic insert acts as the idempotency lock inside the same DB transaction
                self.conn.execute(
                    "INSERT INTO processed_webhooks (event_id, processed_at) VALUES (?, ?)",
                    (event_id, now_ts),
                )
                self.conn.execute(
                    "UPDATE wallets SET balance_kobo = balance_kobo + ? WHERE user_id = ?",
                    (amount_kobo, user_id),
                )
            return 200, {"status": "settled", "event_id": event_id}
        except sqlite3.IntegrityError:
            # Already settled: acknowledge with 200 so the gateway stops retrying
            return 200, {"status": "duplicate_ignored", "event_id": event_id}

    def get_balance(self, user_id: str) -> int:
        return self.conn.execute("SELECT balance_kobo FROM wallets WHERE user_id = ?", (user_id,)).fetchone()[0]


def main() -> None:
    secret = "demo_webhook_secret_local_only"
    receiver = SafeWebhookReceiver(secret=secret)
    now = 1_750_000_000
    body = json.dumps({"event_id": "EVT-9001", "user_id": "USR-101", "amount_kobo": 250_000}).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), f"{now}.".encode("utf-8") + body, hashlib.sha256).hexdigest()

    # 1. First delivery settles the wallet
    code1, res1 = receiver.handle(body, now, sig, now=now)
    # 2. Duplicate retry returns 200 OK without double-crediting
    code2, res2 = receiver.handle(body, now, sig, now=now + 5)
    assert code1 == 200 and res1["status"] == "settled"
    assert code2 == 200 and res2["status"] == "duplicate_ignored"
    assert receiver.get_balance("USR-101") == 250_000

    # 3. Forged signature is rejected
    try:
        receiver.handle(body, now, "invalid_signature", now=now)
        raise AssertionError("Expected forged signature to fail")
    except PermissionError:
        pass

    print(f"Verified webhook demo: first={res1}, retry={res2}, final_balance_kobo={receiver.get_balance('USR-101')}")


if __name__ == "__main__":
    main()
