# Running the six beats on PayPal sandbox

`scripts/sandbox_run.py` runs the six beats in [sandbox-evidence.md](sandbox-evidence.md) as one session. It uses the Permit source tree (the same `SpendPipeline` and `ReleaseVerifier` the service uses) and writes evidence for each beat as it goes.

**Status: the sandbox run has not been done yet.** This script is how to do it. Until a real run is reviewed and its ids are copied into `sandbox-evidence.md`, every beat there stays "not recorded".

## 1. Dry run first (no keys, no network)

```bash
git clone https://github.com/FetchDoge/permit.git
git clone https://github.com/FetchDoge/permit-hackathon.git
cd permit-hackathon
PERMIT_DIR=../permit python3 scripts/sandbox_run.py --dry-run
PERMIT_DIR=../permit python3 -m unittest scripts/test_sandbox_run.py -v   # offline tests
```

The dry run uses Permit's mock rail. A simulated buyer approves each order, so the dry run goes through the same wait-and-resume path as the real run. The output is labelled DRY RUN and is never sandbox evidence.

## 2. The sandbox run

You need a PayPal developer login and a sandbox REST app, plus its sandbox merchant (business) and buyer (personal) accounts. Put the keys in your shell for this session only. Never put them in a file in either repo.

```bash
export PERMIT_PAYPAL_CLIENT_ID=...        # sandbox app client id
export PERMIT_PAYPAL_CLIENT_SECRET=...    # sandbox app secret
export PERMIT_PAYPAL_MERCHANT_ID=...      # sandbox merchant (payee) id
PERMIT_DIR=../permit python3 scripts/sandbox_run.py --sandbox
```

- Four orders need buyer approval: beats 2, 4, 5 and 6. For each one, the script prints an `approval_url`. Open it, log in as the sandbox **buyer**, and approve. The script polls the order's API state, not the checkout page, and resumes the same order. By default it waits 600 s per order (`--approval-timeout`).
- Money moved on the sandbox: $30 in beat 2 and $25 in beat 6. Beats 4 and 5 void their holds. Beat 3 never reaches PayPal.
- In beat 6 the script really sends the capture to PayPal, then throws away the response to simulate a dropped connection. The escrow must go `UNKNOWN`, and `reconcile()` must find the one real capture.

It refuses to start (exit 2, before any network call) if any of the three keys is missing, if `PERMIT_PAYPAL_BASE_URL` is set to anything other than `https://api-m.sandbox.paypal.com`, or if Permit's sandbox client isn't pointed at the sandbox host. It stops at the first failed beat and marks the later ones "not reached". Exit codes: 0 all passed, 1 a beat failed, 2 refused to start.

## 3. What you get

`runs/<UTC time>-<mode>/` (gitignored):

- `evidence.md`: one section per beat, with the same fields as `sandbox-evidence.md`.
- `events.jsonl`: every field and result as it happened, with timestamps.
- `ledger.json`: the full receipt chain, plus the `verify_chain` result in `evidence.md`.

Secrets are never written. The merchant id is recorded only as "present".

## 4. After a real run

1. Read `evidence.md`. Check the capture ids in the PayPal sandbox dashboard.
2. Copy the ids by hand into `docs/sandbox-evidence.md`, and change "not recorded" for a beat only when that beat passed.
3. Record the video. Label sandbox footage as sandbox and mock footage as the mock rail.
