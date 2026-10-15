# Sandbox evidence

This file is evidence of the sandbox procedure, not a claim that the video recording is live.

Status at source `21d7d7ccdf418e46ffd9a6f56aac40491c97d458`: **not recorded.** `README.md` line 111 and `docs/submission-checklist.md` line 62 say the six beats have not been run as one sandbox session. No permit id, order id, authorization id, or capture id from that session exists. Do not fill the blanks from the mock demo. Mock ids start with prefixes such as `mock_` and are not sandbox evidence.

## How to fill this file

Run the procedure in the source `docs/sandbox-runbook.md` as one session. Secrets stay out of both trees. After each beat, copy the real ids and the ledger excerpt from `GET /api/ledger`. If a beat stops, write the exact failure and the receipt that was written. Leave later beats as “not reached”.

Record:

- UTC timestamp at the start and end of the session
- PayPal environment: sandbox, not live
- `PERMIT_PAYPAL_MERCHANT_ID` present or absent (the value stays out of git)
- For each beat: permit id, order id, authorization id, capture id, escrow id, and the receipt `event_type` plus `seq`

## Beat 1 — setup

- Timestamp:
- Permit id:
- Cap cents (expect 5000) and remaining cents:
- Allowlist bound to the configured merchant:
- Receipt:
- Result: not recorded

## Beat 2 — real purchase ($30)

- Timestamp:
- Order id:
- Approval: API order status, not the browser page
- Authorization id:
- Escrow id:
- Capture id:
- Ledger excerpt (ALLOWED, AUTHORIZED, CAPTURED):
- Result: not recorded

## Beat 3 — blocked overspend ($60)

- Timestamp:
- Receipt reason (expect a block before any new authorization):
- PayPal authorize count before and after (expect no new call):
- Result: not recorded

## Beat 4 — e-stop mid-hold

- Timestamp:
- Permit id:
- Order id and authorization id:
- E-stop receipt:
- PayPal void confirmation:
- Release after e-stop:
- Result: not recorded

The source runbook’s beat 4 is e-stop on that permit. Cascade of a parent onto a child is a different verb, `POST /api/permits/<id>/revoke-cascade` (`permit/flow.py` `revoke_cascade`). If the session also runs the cascade, record it in its own subsection. Do not describe e-stop as the cascade.

## Beat 5 — tampered evidence

- Timestamp:
- Escrow id:
- Refusal receipt:
- Capture count unchanged:
- Result: not recorded

## Beat 6 — dropped response, UNKNOWN, reconcile

- Timestamp:
- Escrow state after the timeout (expect UNKNOWN):
- Reconcile outcome (CAPTURED or VOIDED) and the provider id:
- Capture count on the rail (expect one if the money moved):
- Result: not recorded

## Session close

- End timestamp:
- `verify_chain` result:
- What this session does not prove: durability of escrows, pending operations and approvals (only the `--db` ledger is durable), role-separated authentication (one shared bearer token), a demo acceptance-key fallback, hash chain is not a signature, single merchant, completed captures have no refund path in this prototype (`README.md` lines 73–79).
