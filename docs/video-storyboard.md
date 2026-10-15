# Video storyboard

Source: `docs/submission-checklist.md` lines 32–42 in [FetchDoge/permit](https://github.com/FetchDoge/permit) at `21d7d7ccdf418e46ffd9a6f56aac40491c97d458`.

Cut under three minutes. The recording has to say the camera run is the mock rail. It must not say the six beats already ran on the live sandbox. That stays true until [sandbox-evidence.md](sandbox-evidence.md) holds real ids from one session.

| When | Say and show |
| --- | --- |
| 0:00 | The problem. An agent with a wallet can overspend, pay the wrong merchant, or ignore a stop. A budget in a prompt is not a control. |
| 0:20 | The gate. Cap, allowlist, expiry, not revoked. A sub-permit is carved from the parent's remaining cap, so siblings can't overspend it. Hold with `AUTHORIZE`. Capture once, only if the hash matches. The cap returns only when the void is confirmed. |
| 0:45 | Live proof, on screen. `python3 demos/demo_six_beat.py --replay demos/fixtures/demo_transcript.jsonl` and the dashboard at `http://127.0.0.1:8471`. $30 captures. $60 is blocked and PayPal is not called. A $15 sub-permit is carved. Revoke on the parent cascades: child revoked, hold voided, carve released. Mismatched bytes are refused. A dropped capture stays `UNKNOWN`, then reconcile records the one capture. |
| 2:20 | What's next, in one sentence. Running these beats on PayPal's sandbox is the written procedure, not this recording. This recording is the mock rail. |
| 2:35 | `VERIFIED` means the receipt list in this process is internally intact. It is not a PayPal signature. |

Required on-screen labels:

- “mock rail” at 2:20, and anywhere a PayPal id is shown, because those ids come from `MockPayPalClient` (they start with `mock_`).
- The cascade: carved sub-permit, parent revoke, child revoked, hold voided, carve released.
- The UNKNOWN beat, then reconcile to one capture. That beat is in `demos/demo_six_beat.py` (beat 6) and in `tests/test_reconcile.py`. It is not in the `python3 demo.py` path.

## What the 0:45 command does at this revision

Verified on 2026-10-15 at `21d7d7c`. `demos/demo_six_beat.py` accepts `--replay`, `--fast` and `--port` (lines 120–122). There is no `--hold` flag. A fresh clone ships `demos/fixtures/demo_transcript.jsonl`, so the replay needs no API key and no network. The run prints all six beats and ends with `ledger chain: VERIFIED (26 receipts)`, exit 0.

- Without `--fast`, each beat pauses 1.5 s, which is easier to film. `--fast` drops the pauses and finishes in about a second.
- The dashboard is served only while the process runs. The script calls `dash.stop()` before exit (line 304). Film the dashboard during the run, or film the terminal output.
- Without `--replay`, the agent beats need `PERMIT_GROK_CLI` (`README.md` line 55).

The other zero-setup path is `python3 demo.py`, which ends with `ledger chain: VERIFIED (16 receipts)`. It shows grant, allowed capture, blocked overspend and the cascade. It does not show the UNKNOWN beat or the tampered-evidence beat.
