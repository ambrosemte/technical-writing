# Handling Payment Webhooks Safely: Idempotency, Signatures, and Retries

*Personal portfolio writing sample by Ambrose Makai. All code and examples are original and use synthetic data.*

When a customer funds a digital wallet via bank transfer or card checkout, the browser redirect is never the source of truth. Mobile connections drop, users close tabs mid-checkout, and bank transfers happen entirely outside your frontend. Payment gateways solve this with webhooks—asynchronous HTTP `POST` callbacks notifying your backend that a charge succeeded, failed, or reversed.

In practice, webhook endpoints are one of the most common sources of silent financial bugs in wallet and bill-payment systems. Because webhooks sit on public URLs and arrive over unreliable networks, a naive handler that simply reads JSON and credits a wallet will eventually suffer forged requests, double credits, or stuck pending balances. Building a reliable webhook receiver comes down to three concrete disciplines: cryptographic signature verification, database-backed idempotency, and deliberate retry handling.

## 1. Verify Signatures and Reject Replays Before Parsing Trust

Any HTTP endpoint exposed to the public internet will eventually be probed. If your receiver trusts incoming JSON without verifying who sent it, an attacker who discovers your URL can craft a fake `charge.success` payload and credit arbitrary accounts.

Every serious payment gateway signs webhook payloads using a shared secret and an HMAC digest (typically HMAC-SHA256) sent in a request header. Three implementation details separate a safe verifier from a leaky one:

1. **Compute the HMAC over the raw request bytes.** Never parse the JSON into a dictionary and re-serialize it before hashing; whitespace or key-order changes will invalidate valid signatures.
2. **Use constant-time comparison.** Standard string equality (`==`) exits on the first mismatched byte, creating a timing side-channel. Use `hmac.compare_digest()` in Python or `hash_equals()` in PHP.
3. **Bind and check a timestamp window.** Signature verification alone proves the gateway signed the payload *at some point in the past*. To prevent replay attacks where an attacker captures and resends an old valid request, verify that the signed timestamp falls within a tight tolerance window (for example, ±300 seconds of server time).

If signature or timestamp verification fails, reject the request immediately with HTTP `401` or `403` and log a redacted security warning without touching your database.

## 2. Make Settlement Idempotent Inside a Single Database Transaction

Payment gateways guarantee *at-least-once* delivery, not *exactly-once* delivery. If your server takes five seconds to respond because of a database spike, the gateway may time out and retry the exact same event thirty seconds later—or deliver two retries concurrently.

A common mistake is checking `if not already_processed(event_id):` in application memory or in a separate query before updating the wallet. Under concurrent retries, two worker processes can both pass that check simultaneously and credit the customer twice.

The reliable pattern is to enforce uniqueness at the database layer inside the **same ACID transaction** as the wallet credit:

- Create a `processed_webhooks` table with `event_id` as the `PRIMARY KEY` (or a `UNIQUE` index).
- Inside one transaction, `INSERT` the `event_id` first, then `UPDATE` the wallet balance (locking the wallet row with `SELECT ... FOR UPDATE` in PostgreSQL/MySQL).
- If a duplicate retry arrives—even in the exact same millisecond—the `UNIQUE` constraint raises an integrity error, rolling back the duplicate transaction cleanly.

## 3. Working Reference Example

The runnable script [`examples/webhook_handler_demo.py`](../examples/webhook_handler_demo.py) demonstrates signature verification, replay-window enforcement, and transactional idempotency using Python's standard library and SQLite:

```python
try:
    with self.conn:
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
    return 200, {"status": "duplicate_ignored", "event_id": event_id}
```

Notice the return code on `IntegrityError`: **HTTP 200 OK**. Returning `409` or `500` on a duplicate event tells the gateway that delivery failed, which triggers hours of pointless retries and alert noise. Once an event is settled, acknowledging duplicates with `200` keeps both systems quiet and consistent.

## 4. Handle Out-of-Order Callbacks and Slow Processing

Real payment integrations fail in subtler ways than simple duplicates:

- **Slow downstream work:** Never send emails, generate PDF receipts, or call third-party APIs synchronously inside the webhook HTTP handler. Verify the signature, persist the raw event or settle the ledger atomically, return `200`, and dispatch side effects to a background queue.
- **Early or missing webhooks:** Occasionally a gateway fires a webhook *before* your initial checkout HTTP request finishes writing the pending transaction row, or a webhook is lost entirely during a network outage. Treat `pending` as a first-class state: never guess whether a timed-out call succeeded. Pair your webhook endpoint with a scheduled backoff requery job that polls the gateway's transaction-verification API for any row still pending after a threshold, and flags unresolved records for manual review after N attempts.
- **Middleware traps in multi-tenant apps:** Keep webhook routes outside user-session or subscription-gating middleware. If a merchant's subscription lapses minutes after a customer pays, blocking the incoming webhook causes the bank to take the customer's money while the ledger drops the credit.

## Summary Checklist

Before shipping any payment webhook receiver to production, verify five invariants:
1. Raw-body HMAC verification runs with constant-time comparison.
2. Signed timestamps outside a short replay window are rejected.
3. Settlement and `event_id` deduplication commit atomically inside one database transaction.
4. Duplicate events return HTTP `200` without mutating balances.
5. A scheduled requery worker reconciles any pending transactions whose webhooks never arrive.
