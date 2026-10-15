# Permit — hackathon packet

An AI agent that can pay can overspend, pay the wrong merchant, or ignore a stop. A budget written in a prompt is not a control.

Permit puts an enforceable four-clause authority gate between an AI agent and PayPal. Every decision, allowed or blocked, writes a hash-chained receipt.

This repository is the judge-facing packet for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) (deadline 12 Nov 2026, 12:00 pm Pacific). It is not a second implementation. The gate lives in the source tree.

Source, revision cited below: [FetchDoge/permit](https://github.com/FetchDoge/permit) at `b97189a18d2eed274a3e547613ff203a244a973f`.

Video: not uploaded. No public video URL is in the source repo (`docs/submission-checklist.md` line 28).

## Cold start (mock rail)

The runnable demo is the mock rail. It does not call PayPal.

```bash
git clone https://github.com/FetchDoge/permit.git
cd permit
python3 demo.py
```

Run on 2026-10-10 against that revision, the process printed `ledger chain: VERIFIED (15 receipts)`. The path is grant, an allowed capture, a blocked overspend that does not add a PayPal authorize call, then a delegated sub-permit and `revoke_cascade` (`demo.py` line 103). `python3 demo.py --sandbox` does not contact PayPal. It prints the credential requirement and returns (`demo.py` lines 124–128).

`python3 demo_six_beat.py --hold` is the command written in the source checklist. At this revision `demo_six_beat.py` does not accept `--hold`. A fresh clone also has no replay transcript, and a live six-beat run exits if `PERMIT_GROK_CLI` is unset (`README.md` lines 54–56). Use `python3 demo.py` for the zero-setup camera path. The storyboard is in [docs/video-storyboard.md](docs/video-storyboard.md).

## Vocabulary

A permit is the live authority record: cap, allowlist, expiry, revoked, with `remaining = cap − reserved − captured`. Authority is the four-clause check. Authorization is the PayPal hold only. Escrow is that hold plus the release predicate. A receipt is a hash-chain decision. The source comment at `permit/permit.py` line 2 still says “authorization layer”. That word in the comment is not the lock. The formula at lines 4–10 is.

## What it does not claim

Copied from the source README, “What it does not defend (production boundaries)”, lines 72–77:

- All authoritative state lives in memory. A restart loses permits, escrows, revocations, and the ledger.
- The HTTP service has no caller authentication (localhost demo boundary).
- The ledger is a hash chain, not a signature. It detects edits and reordering, but it cannot detect removal of final entries without an external checkpoint.
- It is a single-merchant sandbox prototype, not a claim about all agent payments.
- E-stop voids uncaptured authorizations. A completed capture needs a refund path, which is out of scope.

The integrated sandbox six-beat session is not recorded (`README.md` line 107). [docs/sandbox-evidence.md](docs/sandbox-evidence.md) is the place those ids go after a real run. [docs/claims.md](docs/claims.md) is the list that may appear on the Devpost form or in the video.

## License

MIT. The text is the source repo `LICENSE`, copyright 2026 Marcus Richards.
