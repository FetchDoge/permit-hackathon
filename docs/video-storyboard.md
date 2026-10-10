# Video storyboard

Source: `docs/submission-checklist.md` lines 32–43 in [marsojuji-cmyk/permit](https://github.com/marsojuji-cmyk/permit) at `b97189a18d2eed274a3e547613ff203a244a973f`.

Cut under three minutes. The recording has to say the camera run is the mock rail. It must not say the six beats already ran on the live sandbox.

| When | Say and show |
| --- | --- |
| 0:00 | The problem. An agent with a wallet can overspend, pay the wrong merchant, or ignore a stop. A budget in a prompt is not a control. |
| 0:20 | The gate. Cap, allowlist, expiry, not revoked. A sub-permit is carved from the parent's remaining cap — siblings can't overspend it. Hold with `AUTHORIZE`. Capture once, only if the hash matches. The cap returns only when the void is confirmed. |
| 0:45 | Live proof, on screen. `python3 demo_six_beat.py --hold`. $30 captures. $60 is blocked and PayPal is not called. A $15 sub-permit is carved. Revoke on the parent cascades: child revoked, hold voided, carve released. Tampered bytes are refused. A dropped capture stays `UNKNOWN`, then reconcile records the one capture. |
| 2:20 | What's next, in one sentence. These beats on PayPal's sandbox are the written procedure, not this recording. This recording is the mock rail. |
| 2:35 | `VERIFIED` means the receipt list in this process is internally intact. It is not a PayPal signature and it is not durable. |

Required on-screen labels:

- “mock rail” at 2:20, and anywhere a PayPal id is shown, because those ids come from `MockPayPalClient`.
- The cascade: carved sub-permit, parent revoke, child revoked, hold voided, carve released.
- The UNKNOWN beat, then reconcile to one capture. That beat is in `demo_six_beat.py` and in `tests/test_reconcile.py`. It is not in the `python3 demo.py` closing path.

## What the 0:45 command does at this revision

`demo_six_beat.py` accepts `--replay`, `--fast`, and `--port` (lines 100–103). It does not accept `--hold`. The process calls `dash.stop()` before exit (line 278), so the page does not stay up. A fresh clone has no `demo_transcript.jsonl`. Without `--replay` or `PERMIT_GROK_CLI`, the live agent beats raise (`README.md` lines 54–56).

The zero-setup command that ran on 2026-10-10 is `python3 demo.py` in the source repo. It is the mock rail. It shows the grant, the allowed capture, the blocked overspend, and the cascade through `revoke_cascade`. It does not show the UNKNOWN beat. Say that on camera if the UNKNOWN beat is not in the shot.
