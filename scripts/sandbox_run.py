#!/usr/bin/env python3
"""
Permit: one-session, six-beat run against the PayPal sandbox.

Drives the Permit source tree (FetchDoge/permit) in-process with the same
SpendPipeline and ReleaseVerifier the service uses, and writes evidence for
every beat in the shape of docs/sandbox-evidence.md.

Two modes, and one of them must be chosen explicitly:

    python3 scripts/sandbox_run.py --dry-run     # mock rail, no keys, no network
    python3 scripts/sandbox_run.py --sandbox     # real PayPal sandbox rail

Credentials come from the environment only and are never written anywhere:

    PERMIT_PAYPAL_CLIENT_ID       sandbox REST app client id      (required for --sandbox)
    PERMIT_PAYPAL_CLIENT_SECRET   sandbox REST app secret         (required for --sandbox)
    PERMIT_PAYPAL_MERCHANT_ID     sandbox merchant (payee) id     (required for --sandbox)
    PERMIT_PAYPAL_BASE_URL        optional; must be the sandbox host if set
    PERMIT_DIR                    path to a FetchDoge/permit checkout (or --permit-dir)

Fail closed: --sandbox exits 2 before any network call if a key is missing,
if the base URL is not the PayPal sandbox host, or if the Permit client is
not pointed at the sandbox host.

The output folder (runs/<timestamp>-<mode>/) holds evidence.md, events.jsonl
and ledger.json. A dry run is labelled DRY RUN everywhere and is never sandbox
evidence. A sandbox run is a candidate: review it, then copy the ids into
docs/sandbox-evidence.md by hand.

Exit codes: 0 all beats passed, 1 a beat failed (later beats "not reached"),
2 refused to start (missing keys, wrong host, bad arguments).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SANDBOX_HOST = "https://api-m.sandbox.paypal.com"
REQUIRED_KEYS = (
    "PERMIT_PAYPAL_CLIENT_ID",
    "PERMIT_PAYPAL_CLIENT_SECRET",
    "PERMIT_PAYPAL_MERCHANT_ID",
)
BEATS = [
    (1, "setup"),
    (2, "real purchase ($30)"),
    (3, "blocked overspend ($60)"),
    (4, "e-stop mid-hold"),
    (5, "tampered evidence"),
    (6, "dropped response, UNKNOWN, reconcile"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class BeatFailed(Exception):
    pass


def require(cond: bool, message: str) -> None:
    if not cond:
        raise BeatFailed(message)


# --------------------------------------------------------------- evidence


class Evidence:
    """Collects fields per beat; writes evidence.md and events.jsonl."""

    def __init__(self, out_dir: Path, mode: str):
        self.out_dir = out_dir
        self.mode = mode
        self.dry = mode == "dry-run"
        self.meta: dict[str, str] = {}
        self.beats: dict[int, dict] = {
            n: {"title": t, "fields": [], "result": "not reached"} for n, t in BEATS
        }
        self.close: list[tuple[str, str]] = []
        out_dir.mkdir(parents=True, exist_ok=True)
        self._events = open(out_dir / "events.jsonl", "a", encoding="utf-8")

    def event(self, kind: str, **data) -> None:
        rec = {"ts": utc_now(), "mode": self.mode, "event": kind, **data}
        self._events.write(json.dumps(rec, default=str) + "\n")
        self._events.flush()

    def field(self, beat: int, name: str, value) -> None:
        self.beats[beat]["fields"].append((name, str(value)))
        self.event("field", beat=beat, name=name, value=value)
        print(f"  [beat {beat}] {name}: {value}")

    def result(self, beat: int, text: str) -> None:
        self.beats[beat]["result"] = text
        self.event("result", beat=beat, result=text)

    def write(self) -> Path:
        label = (
            "DRY RUN (mock rail). NOT sandbox evidence. Ids starting with `mock_` "
            "come from MockPayPalClient."
            if self.dry
            else "SANDBOX RUN, candidate evidence. Review it before copying any id "
            "into docs/sandbox-evidence.md."
        )
        lines = [f"# Six-beat run evidence ({self.mode})", "", f"**{label}**", ""]
        for k, v in self.meta.items():
            lines.append(f"- {k}: {v}")
        for n, _ in BEATS:
            b = self.beats[n]
            lines += ["", f"## Beat {n}: {b['title']}", ""]
            for name, value in b["fields"]:
                lines.append(f"- {name}: {value}")
            lines.append(f"- Result: {b['result']}")
        lines += ["", "## Session close", ""]
        for name, value in self.close:
            lines.append(f"- {name}: {value}")
        lines.append("")
        path = self.out_dir / "evidence.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        self._events.close()
        return path


# --------------------------------------------------------------- rail proxy


class CountingRail:
    """
    Wraps the PayPal client. Counts provider calls so beats 3, 5 and 6 can
    show "no new call" or "exactly one capture". When drop_next_capture is
    armed, the next capture is sent to the provider and applied there, then
    its response is discarded and a PayPalTimeout is raised. That is the
    dropped-response case reconcile() exists for. Nothing else is altered.
    """

    def __init__(self, inner, timeout_exc):
        self._inner = inner
        self._timeout_exc = timeout_exc
        self.calls = {"authorize": 0, "authorize_order": 0, "capture": 0, "void": 0}
        self.drop_next_capture = False

    @property
    def merchant_account_id(self):
        return getattr(self._inner, "merchant_account_id", None)

    def authorize(self, amount_cents, merchant_id, idempotency_key=None):
        self.calls["authorize"] += 1
        return self._inner.authorize(amount_cents, merchant_id, idempotency_key=idempotency_key)

    def get_authorization(self, auth_id):
        return self._inner.get_authorization(auth_id)

    def capture(self, auth_id, amount_cents, idempotency_key):
        self.calls["capture"] += 1
        result = self._inner.capture(auth_id, amount_cents, idempotency_key)
        if self.drop_next_capture:
            self.drop_next_capture = False
            raise self._timeout_exc("capture response dropped by sandbox_run.py (beat 6)")
        return result

    def void(self, auth_id):
        self.calls["void"] += 1
        return self._inner.void(auth_id)

    def __getattr__(self, name):
        attr = getattr(self._inner, name)  # AttributeError passes through
        if name == "authorize_order" and callable(attr):
            def counted(*a, **kw):
                self.calls["authorize_order"] += 1
                return attr(*a, **kw)
            return counted
        return attr

    def authorize_total(self) -> int:
        return self.calls["authorize"] + self.calls["authorize_order"]


# --------------------------------------------------------------- dry-run rail


class NeedsPayerApproval(Exception):
    """Same name and fields as the sandbox client's exception (flow.py matches by name)."""

    def __init__(self, order_id: str, approval_url: str):
        super().__init__(f"order {order_id} needs payer approval")
        self.order_id = order_id
        self.approval_url = approval_url


def _approval_mock(base):
    """
    MockPayPalClient that behaves like the sandbox approval flow: every new
    order first needs payer approval, and the simulated buyer approves it
    before the first resume poll after that. This keeps the dry run on the
    same spend -> wait -> resume path the sandbox run uses.
    """

    class ApprovalMock(base):
        def __init__(self):
            super().__init__()
            self._orders: dict[str, dict] = {}

        def authorize(self, amount_cents, merchant_id, idempotency_key=None):
            order_id = f"mock_order_{len(self._orders) + 1:03d}"
            self._orders[order_id] = {"approved": False, "key": idempotency_key}
            raise NeedsPayerApproval(order_id, f"mock://approve/{order_id}")

        def authorize_order(self, order_id, amount_cents, merchant_id, idempotency_key=None):
            order = self._orders[order_id]
            if not order["approved"]:
                order["approved"] = True  # the simulated buyer approves now
                raise NeedsPayerApproval(order_id, f"mock://approve/{order_id}")
            return base.authorize(self, amount_cents, merchant_id,
                                  idempotency_key=order["key"])

    return ApprovalMock


# --------------------------------------------------------------- run


def git_rev(path: Path) -> str:
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(path), "status", "--porcelain"], text=True,
            stderr=subprocess.DEVNULL).strip()
        return sha + (" (uncommitted changes present)" if dirty else "")
    except Exception:
        return "unknown (not a git checkout)"


def preflight(args) -> tuple[str | None, list[str]]:
    """Return (mode, problems). Never prints secret values."""
    problems: list[str] = []
    if args.dry_run == args.sandbox:
        problems.append("choose exactly one of --dry-run or --sandbox")
        return None, problems
    mode = "dry-run" if args.dry_run else "sandbox"
    if mode == "sandbox":
        for k in REQUIRED_KEYS:
            if not os.environ.get(k, "").strip():
                problems.append(f"{k} is not set")
        base = os.environ.get("PERMIT_PAYPAL_BASE_URL", "").strip().rstrip("/")
        if base and base != SANDBOX_HOST:
            problems.append(
                f"PERMIT_PAYPAL_BASE_URL must be {SANDBOX_HOST} (live PayPal is refused)")
    return mode, problems


def run(args) -> int:
    mode, problems = preflight(args)
    if problems:
        for p in problems:
            print(f"REFUSED: {p}", file=sys.stderr)
        if mode == "sandbox":
            print("No network call was made. Set the keys in your shell (never in a "
                  "file in this repo) and run again, or use --dry-run.", file=sys.stderr)
        return 2

    permit_dir = Path(args.permit_dir or os.environ.get("PERMIT_DIR") or
                      Path(__file__).resolve().parents[2] / "permit").resolve()
    if not (permit_dir / "permit" / "flow.py").is_file():
        print(f"REFUSED: {permit_dir} is not a FetchDoge/permit checkout "
              "(set PERMIT_DIR or --permit-dir)", file=sys.stderr)
        return 2
    sys.path.insert(0, str(permit_dir))

    # Predicate A (acceptance signature) is not used by these beats. Newer
    # Permit revisions refuse to build a verifier without a key, so give this
    # process an ephemeral random one unless the caller set their own.
    ephemeral_key = False
    if not os.environ.get("PERMIT_ACCEPTANCE_KEY"):
        os.environ["PERMIT_ACCEPTANCE_KEY"] = secrets.token_hex(32)
        ephemeral_key = True

    import warnings
    warnings.simplefilter("ignore", RuntimeWarning)
    from permit.flow import ApprovalRequired, SpendPipeline
    from permit.ledger import Ledger
    from permit.permit import PermitStore
    from settlement.paypal_client import MockPayPalClient, PayPalTimeout
    from settlement.verifier import Evidence as Delivery, PredicateType, ReleaseVerifier

    if mode == "sandbox":
        from settlement import sandbox_client
        if getattr(sandbox_client, "BASE", "").rstrip("/") != SANDBOX_HOST:
            print(f"REFUSED: settlement/sandbox_client.py BASE is not {SANDBOX_HOST}",
                  file=sys.stderr)
            return 2
        merchant = os.environ["PERMIT_PAYPAL_MERCHANT_ID"].strip()
        inner = sandbox_client.SandboxPayPalClient(
            os.environ["PERMIT_PAYPAL_CLIENT_ID"].strip(),
            os.environ["PERMIT_PAYPAL_CLIENT_SECRET"].strip(),
            merchant_account_id=merchant,
        )
    else:
        merchant = "dry_run_merchant"
        inner = _approval_mock(MockPayPalClient)()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_root = Path(args.out or Path(__file__).resolve().parents[1] / "runs")
    ev = Evidence(out_root / f"{stamp}-{mode}", mode)
    ev.meta = {
        "Session start (UTC)": utc_now(),
        "PayPal environment": ("sandbox (" + SANDBOX_HOST + ")") if mode == "sandbox"
        else "none: mock rail (MockPayPalClient), no network",
        "PERMIT_PAYPAL_MERCHANT_ID": "present (value kept out of this file)"
        if mode == "sandbox" else "not used (dry run)",
        "Permit source": git_rev(permit_dir),
        "Acceptance key": "ephemeral random key for this process (predicate A unused)"
        if ephemeral_key else "from PERMIT_ACCEPTANCE_KEY (predicate A unused)",
    }
    ev.event("start", permit_source=ev.meta["Permit source"])
    print(f"== Permit six-beat run, mode: {mode.upper()} ==")
    if mode == "dry-run":
        print("   DRY RUN: mock rail. Nothing here is sandbox evidence.")

    rail = CountingRail(inner, PayPalTimeout)
    ledger = Ledger()
    permits = PermitStore(ledger=ledger)
    verifier = ReleaseVerifier(rail, permits, ledger=ledger)
    flow = SpendPipeline(permits, rail, verifier, ledger=ledger)

    def grant(cap_cents: int, agent: str):
        return permits.grant(agent_id=agent, cap_cents=cap_cents, allowlist=[merchant],
                             expiry=datetime.now(timezone.utc) + timedelta(hours=1))

    def receipts_for(**match) -> list[str]:
        out = []
        for r in ledger.receipts():
            if all(r.payload.get(k) == v for k, v in match.items()):
                out.append(f"{r.event_type}#{r.seq}")
        return out

    def spend_through_approval(beat: int, permit_id: str, amount: int, digest: str):
        """spend(); if the payer must approve, wait and resume the SAME order."""
        try:
            attempt = flow.spend(permit_id, amount, merchant, PredicateType.D, digest)
        except ApprovalRequired as appr:
            ev.field(beat, "Order id", appr.order_id)
            ev.field(beat, "Approval", "API order status, not the browser page")
            if mode == "dry-run":
                print(f"  (dry run: simulated buyer approves {appr.order_id})")
            else:
                print(f"\n  >>> Approve this order as the sandbox BUYER in a browser:\n"
                      f"      {appr.approval_url}\n"
                      f"      Waiting up to {args.approval_timeout:.0f}s; polling the order API.\n")
            ev.event("approval_required", beat=beat, order_id=appr.order_id,
                     approval_url=appr.approval_url)
            deadline = time.monotonic() + args.approval_timeout
            pending = appr
            while True:
                try:
                    attempt = flow.resume_operation(pending)
                    break
                except ApprovalRequired as still:
                    pending = still
                    if time.monotonic() > deadline:
                        raise BeatFailed(
                            f"payer approval not seen within {args.approval_timeout:.0f}s "
                            f"(order {appr.order_id}); the reservation stays held, "
                            "run e-stop or let the 15-minute TTL reap it")
                    time.sleep(args.poll_interval)
        return attempt

    def escrow(eid):
        e = verifier.get_escrow(eid)
        require(e is not None, f"escrow {eid} not found")
        return e

    artifact = b"permit sandbox run deliverable v1"
    digest = hashlib.sha256(artifact).hexdigest()
    failed_at = None

    try:
        # Beat 1: setup
        n = 1
        ev.field(n, "Timestamp", utc_now())
        p1, r = grant(5000, "sandbox_run_agent")
        ev.field(n, "Permit id", p1.permit_id)
        ev.field(n, "Cap cents (expect 5000) and remaining cents",
                 f"{p1.cap_cents} / {p1.remaining_cents()}")
        ev.field(n, "Allowlist bound to the configured merchant",
                 "yes" if list(p1.allowlist) == [merchant] else f"NO: {p1.allowlist}")
        ev.field(n, "Receipt", f"{r.event_type}#{r.seq}")
        require(p1.remaining_cents() == 5000, "remaining_cents != 5000")
        ev.result(n, "passed")

        # Beat 2: real purchase ($30)
        n = 2
        ev.field(n, "Timestamp", utc_now())
        a2 = spend_through_approval(n, p1.permit_id, 3000, digest)
        require(a2.allowed and a2.escrow_id, f"spend not allowed: {a2.reason}")
        e2 = escrow(a2.escrow_id)
        ev.field(n, "Authorization id", e2.paypal_auth_id)
        ev.field(n, "Escrow id", a2.escrow_id)
        res2 = flow.release(a2.escrow_id, Delivery(delivered_bytes=artifact))
        require(res2.released and res2.capture, f"release failed: {res2.reason}")
        ev.field(n, "Capture id", res2.capture.capture_id)
        ev.field(n, "Ledger excerpt (ALLOWED, AUTHORIZED, CAPTURED)",
                 ", ".join(receipts_for(permit_id=p1.permit_id)))
        ev.result(n, "passed")

        # Beat 3: blocked overspend ($60)
        n = 3
        ev.field(n, "Timestamp", utc_now())
        before = rail.authorize_total()
        a3 = flow.spend(p1.permit_id, 6000, merchant, PredicateType.D, digest)
        after = rail.authorize_total()
        ev.field(n, "Receipt reason (expect a block before any new authorization)",
                 f"{'BLOCKED' if not a3.allowed else 'ALLOWED'} {a3.reason} "
                 f"({', '.join(f'{x.event_type}#{x.seq}' for x in a3.receipts)})")
        ev.field(n, "PayPal authorize count before and after (expect no new call)",
                 f"{before} -> {after}")
        require(not a3.allowed, "overspend was allowed")
        require(before == after, "a PayPal authorize call was made for a blocked spend")
        ev.result(n, "passed")

        # Beat 4: e-stop mid-hold
        n = 4
        ev.field(n, "Timestamp", utc_now())
        p4, _ = grant(5000, "sandbox_run_estop")
        ev.field(n, "Permit id", p4.permit_id)
        a4 = spend_through_approval(n, p4.permit_id, 1000, digest)
        require(a4.allowed and a4.escrow_id, f"spend not allowed: {a4.reason}")
        e4 = escrow(a4.escrow_id)
        ev.field(n, "Authorization id", e4.paypal_auth_id)
        stop = flow.estop(p4.permit_id)
        if hasattr(stop, "receipt"):
            receipt4, voided4 = stop.receipt, list(stop.voided)
        else:  # older revisions return (receipt, voided)
            receipt4, voided4 = stop
        ev.field(n, "E-stop receipt", f"{receipt4.event_type}#{receipt4.seq}")
        provider4 = rail.get_authorization(e4.paypal_auth_id).status
        ev.field(n, "PayPal void confirmation",
                 f"voided={voided4}; provider authorization status={provider4}")
        res4 = flow.release(a4.escrow_id, Delivery(delivered_bytes=artifact))
        ev.field(n, "Release after e-stop", f"released={res4.released} reason={res4.reason}")
        require(p4.revoked, "permit not revoked")
        require(a4.escrow_id in voided4, "e-stop did not confirm the void")
        require(provider4 == "VOIDED", f"provider status {provider4}, expected VOIDED")
        require(not res4.released, "release after e-stop was not refused")
        ev.result(n, "passed")

        # Beat 5: tampered evidence
        n = 5
        ev.field(n, "Timestamp", utc_now())
        p5, _ = grant(5000, "sandbox_run_tamper")
        a5 = spend_through_approval(n, p5.permit_id, 1500, digest)
        require(a5.allowed and a5.escrow_id, f"spend not allowed: {a5.reason}")
        ev.field(n, "Escrow id", a5.escrow_id)
        e5 = escrow(a5.escrow_id)
        captures_before = rail.calls["capture"]
        res5 = flow.release(a5.escrow_id, Delivery(delivered_bytes=b"tampered bytes"))
        refusal = [x for x in receipts_for(escrow_id=a5.escrow_id) if x.startswith("REFUSED")]
        ev.field(n, "Refusal receipt", ", ".join(refusal) or f"none (reason={res5.reason})")
        ev.field(n, "Capture count unchanged",
                 f"{captures_before} -> {rail.calls['capture']}")
        provider5 = rail.get_authorization(e5.paypal_auth_id).status
        ev.field(n, "Hold voided and reservation released",
                 f"provider status={provider5}; remaining={p5.remaining_cents()} of 5000")
        require(not res5.released, "tampered evidence was released")
        require(rail.calls["capture"] == captures_before, "a capture was attempted")
        require(provider5 == "VOIDED", f"provider status {provider5}, expected VOIDED")
        require(p5.remaining_cents() == 5000, "reservation not released")
        ev.result(n, "passed")

        # Beat 6: dropped response, UNKNOWN, reconcile
        n = 6
        ev.field(n, "Timestamp", utc_now())
        p6, _ = grant(5000, "sandbox_run_unknown")
        a6 = spend_through_approval(n, p6.permit_id, 2500, digest)
        require(a6.allowed and a6.escrow_id, f"spend not allowed: {a6.reason}")
        e6 = escrow(a6.escrow_id)
        captures_before = rail.calls["capture"]
        rail.drop_next_capture = True
        res6 = flow.release(a6.escrow_id, Delivery(delivered_bytes=artifact))
        state6 = escrow(a6.escrow_id).state
        ev.field(n, "Escrow state after the timeout (expect UNKNOWN)",
                 f"{state6} (release: released={res6.released} reason={res6.reason})")
        require(state6 == "UNKNOWN", f"escrow state {state6}, expected UNKNOWN")
        rec = verifier.reconcile(a6.escrow_id)
        ev.field(n, "Reconcile outcome (CAPTURED or VOIDED) and the provider id",
                 f"{rec.outcome} {rec.capture.capture_id if rec.capture else e6.paypal_auth_id}")
        provider6 = rail.get_authorization(e6.paypal_auth_id).status
        ev.field(n, "Capture count on the rail (expect one if the money moved)",
                 f"{rail.calls['capture'] - captures_before} capture call(s); "
                 f"provider status={provider6}")
        require(rec.resolved, f"reconcile did not resolve: {rec.outcome}")
        require(rail.calls["capture"] - captures_before == 1, "more than one capture call")
        ev.result(n, f"passed ({rec.outcome})")
    except Exception as exc:  # fail closed: stop here, mark the rest not reached
        failed_at = n
        ev.result(n, f"FAILED: {type(exc).__name__}: {exc}")
        print(f"\n  BEAT {n} FAILED: {exc}", file=sys.stderr)

    ok, reason = ledger.verify_chain()
    ev.close = [
        ("End timestamp (UTC)", utc_now()),
        ("verify_chain result", f"{'VERIFIED' if ok else 'BROKEN: ' + reason} "
                                f"({len(ledger)} receipts)"),
        ("Provider calls", json.dumps(rail.calls)),
        ("What this session does not prove",
         "durability of escrows, pending operations and approvals; role-separated "
         "authentication; hash chain is not a signature; single merchant; completed "
         "captures have no refund path in this prototype"),
    ]
    (ev.out_dir / "ledger.json").write_text(json.dumps(
        [{"seq": r.seq, "event": r.event_type, "hash": r.hash, "prev_hash": r.prev_hash,
          "timestamp": r.timestamp, "payload": r.payload} for r in ledger.receipts()],
        indent=2, default=str), encoding="utf-8")
    path = ev.write()
    print(f"\n== ledger chain: {'VERIFIED' if ok else 'BROKEN'} ({len(ledger)} receipts)")
    print(f"== evidence: {path}")
    if mode == "dry-run":
        print("== DRY RUN: do not copy these ids into docs/sandbox-evidence.md")
    return 1 if (failed_at or not ok) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="mock rail, no keys, no network")
    ap.add_argument("--sandbox", action="store_true", help="real PayPal sandbox rail")
    ap.add_argument("--permit-dir", help="FetchDoge/permit checkout (default $PERMIT_DIR or ../permit)")
    ap.add_argument("--out", help="output root (default runs/)")
    ap.add_argument("--approval-timeout", type=float, default=600.0,
                    help="seconds to wait for each payer approval (default 600)")
    ap.add_argument("--poll-interval", type=float, default=5.0)
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
