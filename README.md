# Permit — hackathon packet

An AI agent that can pay can overspend, pay the wrong merchant, or ignore a stop. A budget written in a prompt is not a control.

Permit puts an enforceable four-clause authority gate between an AI agent and PayPal. Every decision, allowed or blocked, writes a hash-chained receipt.

This repository is the judge-facing packet for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) (deadline 12 Nov 2026, 12:00 pm Pacific). It is not a second implementation. The gate lives in the source tree.

Source, revision cited below: [FetchDoge/permit](https://github.com/FetchDoge/permit) at `21d7d7ccdf418e46ffd9a6f56aac40491c97d458` (`main`, 2026-10-15).

Video: not uploaded. No public video URL is in the source repo (`docs/submission-checklist.md` line 28).

## Cold start (mock rail)

The runnable demo is the mock rail. It does not call PayPal.

```bash
git clone https://github.com/FetchDoge/permit.git
cd permit
python3 demo.py
```

Run on 2026-10-15 against that revision, the process printed `ledger chain: VERIFIED (16 receipts)`. The path is grant, an allowed capture, a blocked overspend that does not add a PayPal authorize call, then a delegated sub-permit and `revoke_cascade`. `python3 demo.py --sandbox` does not contact PayPal. It prints the credential requirement and returns (`demo.py` lines 124–128).

The six-beat camera path also needs no setup. A fresh clone ships a recorded agent transcript:

```bash
python3 demos/demo_six_beat.py --fast --replay demos/fixtures/demo_transcript.jsonl
```

On 2026-10-15 at that revision it ran all six beats on the mock rail and printed `ledger chain: VERIFIED (26 receipts)`. There is no `--hold` flag. A live run without `--replay` needs `PERMIT_GROK_CLI` (`README.md` line 55). The storyboard is in [docs/video-storyboard.md](docs/video-storyboard.md).

Tests at that revision: `python -m pytest -q` printed `389 passed, 1 skipped` (390 collected), matching the green `ci` run for `21d7d7c`.

## Vocabulary

A permit is the live authority record: cap, allowlist, expiry, revoked, with `remaining = cap − reserved − captured`. Authority is the four-clause check. Authorization is the PayPal hold only. Escrow is that hold plus the release predicate. A receipt is a hash-chain decision. The source comment at `permit/permit.py` line 2 still says “authorization layer”. That word in the comment is not the lock. The formula at lines 4–10 is.

## What it does not claim

Summarized from the source README, “What it does not defend (production boundaries)”, lines 73–79:

- With `--db PATH` the SQLite ledger is durable and restores permits and reservations, but not escrows, pending operations, or approvals. Default (in-memory) mode loses permits, escrows, revocations, and the ledger on restart.
- HTTP POSTs need one shared bearer token (`PERMIT_API_TOKEN`), with no role split between principal and agent. GETs, including `/api/ledger`, are unauthenticated. The server binds to 127.0.0.1.
- Predicate A acceptance falls back to a hardcoded demo key when `PERMIT_ACCEPTANCE_KEY` is unset.
- The ledger is a hash chain, not a signature. It detects edits and reordering, but it cannot detect removal of final entries without an external checkpoint.
- It is a single-merchant sandbox prototype, not a claim about all agent payments.
- E-stop voids uncaptured authorizations. A completed capture needs a refund path, which is out of scope.

The integrated sandbox six-beat session is not recorded (`README.md` line 111). [docs/sandbox-evidence.md](docs/sandbox-evidence.md) is the place those ids go after a real run. [docs/claims.md](docs/claims.md) is the list that may appear on the Devpost form or in the video.

## License

MIT. The text is the source repo `LICENSE`, copyright 2026 Marcus Richards.
