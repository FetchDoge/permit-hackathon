# Claims that match the source tree

Source: [FetchDoge/permit](https://github.com/FetchDoge/permit) at `21d7d7ccdf418e46ffd9a6f56aac40491c97d458` (`main`, 2026-10-15). Line numbers below are for that revision.

Only the bullets under “May appear on the form or in the video” are safe to say. Each one is no stronger than the cited line or test. The “Withheld” list is wording that this revision does not prove as written.

## May appear on the form or in the video

- An agent that can pay still needs an enforceable gate. A budget in a prompt is not that gate. Source `README.md` line 9.
- The authority check is four clauses: `amount <= remaining`, merchant in the allowlist, `now < expiry`, and not revoked. `remaining = cap − reserved − captured`. Source `README.md` lines 15–24 and `permit/permit.py` lines 4–10.
- The authority boundary accepts positive integers. Source `README.md` line 26.
- A blocked check does not call PayPal. Source `README.md` line 27. Test `tests/test_flow.py` `test_blocked_spend_never_touches_paypal`. `permit/` is barred from importing a PayPal client by `tests/test_permit.py` `test_no_paypal_imports_in_permit_module`.
- Delegation only subdivides: the child cap cannot exceed the parent’s remaining, the child allowlist cannot add merchants, and the child cannot outlive the parent. The carve is reserved on the parent. Source `README.md` line 30, `permit/permit.py` `delegate`, `permit/flow.py` `delegate` (line 707).
- A child capture rolls reserved into captured on the ancestors. Test `tests/test_delegation.py` `test_child_spend_and_capture_roll_up_to_parent`.
- `revoke_cascade` revokes the permit and its descendants, voids in-flight holds in that subtree, and releases unspent carves. Source `README.md` line 66 and `permit/flow.py` `revoke_cascade` (line 788). `python3 demo.py` calls it in step 4.
- E-stop revokes the permit and every descendant, and voids the in-flight holds it can reach across that subtree. Escrows already in `UNKNOWN` are left for `reconcile()`, not voided. Source `README.md` line 65, `permit/flow.py` `estop` (line 819, which calls `estop_cascade`). Tests `tests/test_flow.py` `test_parent_estop_voids_in_flight_child_hold` and `tests/test_tighten.py` `test_tighten_then_estop_still_cascades`.
- Release after a narrowed expiry is refused. Source `README.md` line 63. Tests `tests/test_flow.py` `test_release_refused_after_tightened_expiry` and `test_release_refused_after_ancestor_tightened_expiry`.
- A capture timeout leaves the escrow UNKNOWN. `reconcile()` records CAPTURED if the provider captured, otherwise it voids. Source `README.md` line 68. Tests in `tests/test_reconcile.py`, including `test_reconcile_b_timeout_after_apply_no_double_capture`.
- When a registered escrow’s void times out, it waits in `CLEANUP_PENDING` with the reservation held until `retry_cleanup()` confirms the void. Source `README.md` line 69. Test `tests/test_settlement.py` `test_p1_4_predicate_fail_void_timeout_cleanup_pending_then_retry`.
- The capture idempotency key is `{permit_id}:{auth_id}:capture`, sent as `PayPal-Request-Id`. Source `README.md` line 29 and `settlement/verifier.py` `_capture_key` (line 181).
- Receipts are a SHA-256 hash chain. `verify_chain()` runs before capture. Source `README.md` line 32 and `permit/ledger.py` `verify_chain` (line 98).
- Every HTTP POST needs the bearer token in `PERMIT_API_TOKEN`. With the token unset, every mutating call is refused. Source `README.md` line 75 and `server.py` `_authorized`. Test `tests/test_server.py` `test_mutating_routes_require_bearer_token`.
- With `--db PATH`, the receipt ledger is SQLite-backed and survives a restart. Default mode is in memory. Source `README.md` line 74 and `server.py` `--db`. Tests in `tests/test_sqlite_ledger.py` and `tests/test_durable_append_concurrency.py`.
- `python3 demo.py` is the mock rail. It does not use the network. Source `demo.py` lines 1–2. On 2026-10-15 at this revision it printed `ledger chain: VERIFIED (16 receipts)`. `python3 demo.py --sandbox` prints the credential requirement and returns before any PayPal call (`demo.py` lines 124–128).
- `demos/demo_six_beat.py` is also the mock rail. A fresh clone ships a recorded agent transcript, so the six beats replay offline with no API key: `python3 demos/demo_six_beat.py --fast --replay demos/fixtures/demo_transcript.jsonl`. On 2026-10-15 at this revision it ran all six beats (grant, $30 capture, $60 blocked, $15 sub-permit plus parent cascade, mismatched evidence refused, dropped capture to UNKNOWN to reconcile) and printed `ledger chain: VERIFIED (26 receipts)`, exit 0. Source `README.md` line 55 and `demos/fixtures/README.md` (fixture provenance). A live run without `--replay` needs `PERMIT_GROK_CLI`.
- Tests: `python -m pytest -q` at this revision printed `389 passed, 1 skipped` (390 collected), run locally on 2026-10-15. The green `ci` run for `21d7d7c` shows the same result on Python 3.11 and 3.12.
- The integrated sandbox six-beat session is not recorded. Source `README.md` line 111, `docs/submission-checklist.md` line 62, and this packet’s [sandbox-evidence.md](sandbox-evidence.md).
- The Oct 2 sandbox spike made real REST calls (OAuth, order, authorize, capture, void) against PayPal sandbox. Its report left the tree in `3f88feb` and is readable with `git show 3f88feb^:spike-report.md`. Source `README.md` line 110. That spike is not the six-beat session.
- No public video URL is in the source repo. `docs/submission-checklist.md` line 28.
- Production boundaries, six bullets. Source `README.md` lines 73–79. Also in this packet’s README.
- The agent is not the holder of the PayPal secret. Source `README.md` lines 9 and 100.
- License is Apache-2.0, copyright 2026 Marcus Richards. Source `LICENSE` and `NOTICE`.
- The hackathon deadline named in the source README is Nov 12, 2026. Source `README.md` line 11.

## Withheld until the source tree shows them

These sentences are not claims of this packet.

- Any statement that the six sandbox beats have been completed, or that the video shows the sandbox session. Not recorded. The storyboard forbids saying the recording is the live rail.
- `python3 demos/demo_six_beat.py --hold`, or any page that stays up until Ctrl+C. `demos/demo_six_beat.py` accepts only `--replay`, `--fast` and `--port` (lines 120–122). It calls `dash.stop()` before exit (line 304).
- “Every void failure keeps the reservation.” The registered-escrow path is tested (above). This packet has not re-checked every other void path line by line at this revision.
- Predicate A acceptance is fail-closed. At this revision it falls back to a hardcoded demo key when `PERMIT_ACCEPTANCE_KEY` is unset (`README.md` line 76, open issue #35).
- The calibration score S is a safety signal. It is advisory, never blocks a spend, and its weights are uncalibrated fixtures (`README.md` line 98).
- Any test count other than the one above. Older pages said 187, 337 and 344. Those were different revisions.
