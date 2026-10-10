# Claims that match the source tree

Source: [marsojuji-cmyk/permit](https://github.com/marsojuji-cmyk/permit) at `b97189a18d2eed274a3e547613ff203a244a973f`.

Only the bullets under “May appear on the form or in the video” are safe to say. Each one is no stronger than the cited line. The “Withheld” list is checklist or README wording that this revision does not prove as written.

## May appear on the form or in the video

- An agent that can pay still needs an enforceable gate. A budget in a prompt is not that gate. Source `README.md` line 9. Storyboard `docs/submission-checklist.md` line 36.
- The authority check is four clauses: `amount <= remaining`, merchant in the allowlist, `now < expiry`, and not revoked. `remaining = cap − reserved − captured`. Source `README.md` lines 17–23 and `permit/permit.py` lines 4–10.
- The authority boundary accepts positive integers. Source `README.md` line 26.
- A blocked check does not call PayPal. Source `README.md` line 27. Test `tests/test_flow.py` `test_blocked_spend_never_touches_paypal`. `permit/` is barred from importing a PayPal client by `tests/test_permit.py` `test_no_paypal_imports_in_permit_module`.
- Delegation only subdivides: the child cap cannot exceed the parent’s remaining, the child allowlist cannot add merchants, and the child cannot outlive the parent. The carve is reserved on the parent. Source `README.md` line 30 and `permit/permit.py` `delegate`.
- A child capture rolls reserved into captured on the ancestors. Test `tests/test_delegation.py` `test_child_spend_and_capture_roll_up_to_parent`.
- `revoke_cascade` revokes the permit and its descendants, voids in-flight holds in that subtree, and releases unspent carves. Source `README.md` line 65 and `permit/flow.py` lines 584–606. `demo.py` line 103 calls that function. On 2026-10-10, `python3 demo.py` printed `REVOKED_CASCADE` and `ledger chain: VERIFIED (15 receipts)`.
- E-stop revokes the named permit and voids in-flight holds that path can reach. Source `README.md` line 64 and `permit/flow.py` lines 614–627. It is not the cascade verb.
- A capture timeout leaves the escrow UNKNOWN. `reconcile()` records CAPTURED if the provider captured, otherwise it voids. Source `README.md` line 67. Tests in `tests/test_reconcile.py`, including `test_reconcile_b_timeout_after_apply_no_double_capture`.
- The capture idempotency key is `{permit_id}:{auth_id}:capture`, sent as `PayPal-Request-Id`. Source `README.md` line 29 and `settlement/verifier.py` `_capture_key`.
- Receipts are a SHA-256 hash chain. `verify_chain()` runs before capture. Source `README.md` line 32 and `permit/ledger.py`.
- `python3 demo.py` is the mock rail. It does not use the network. Source `demo.py` lines 1–2. `python3 demo.py --sandbox` returns before any PayPal call (`demo.py` lines 124–128).
- `demo_six_beat.py` is also the mock rail. Its header says so (`demo_six_beat.py` line 1). A live run needs `PERMIT_GROK_CLI` or `--replay` of a transcript. The transcript is gitignored (`README.md` lines 54–56 and 105).
- The integrated sandbox six-beat session is not recorded. Source `README.md` line 107, `docs/sandbox-runbook.md` opening status, `docs/submission-checklist.md` line 62.
- No public video URL is in the source repo. `docs/submission-checklist.md` line 28.
- `README.md` line 102 states that 187 tests pass. On 2026-10-10, `python -m pytest -q` in a clone of this revision printed `187 passed in 6.94s`.
- Production boundaries, five bullets. Source `README.md` lines 73–77. Also in this packet’s README.
- The agent is not the holder of the PayPal secret. Source `README.md` lines 9 and 96.
- License is MIT, copyright 2026 Marcus Richards. Source `LICENSE`.
- Hackathon deadline named in the source README is Nov 12, 2026. Source `README.md` line 11.

## Withheld until the source tree shows them

These sentences appear in the source checklist or README. They are not claims of this packet.

- `python3 demo_six_beat.py --hold` opens a page that stays up until Ctrl+C. Checklist line 15. `demo_six_beat.py` lines 100–103 have no `--hold`. Line 278 calls `dash.stop()`.
- A fresh `python3 demo_six_beat.py --fast` reaches `VERIFIED` with no API key and no network. Checklist line 11. `README.md` lines 54–56 say an unset `PERMIT_GROK_CLI` exits 1, and a fresh clone has no transcript.
- “Release after expiry” voids every hold once any narrowed expiry has passed. `README.md` line 62. Capture admission checks `permit.revoked` and `permit.expiry` (`settlement/verifier.py` line 199), which is the granted expiry field.
- “Void fails” always keeps the reservation. `README.md` line 68 describes the registered-escrow `CLEANUP_PENDING` path. The unregistered outstanding-hold path in `permit/flow.py` still calls `settle_void` when the provider void raises.
- The six sandbox beats have been completed, or the video is that sandbox session. Not recorded. The storyboard line 43 forbids saying the recording is the live rail.
- E-stop alone revokes descendants. `server.py` lines 17–19 say that. `permit/flow.py` `estop` revokes the one permit. Descendants are `revoke_cascade`.
