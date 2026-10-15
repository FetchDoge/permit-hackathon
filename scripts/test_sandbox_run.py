"""
Offline tests for scripts/sandbox_run.py. No keys, no network.

    PERMIT_DIR=../permit python3 -m unittest scripts/test_sandbox_run.py -v
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("sandbox_run.py")
KEYS = ("PERMIT_PAYPAL_CLIENT_ID", "PERMIT_PAYPAL_CLIENT_SECRET",
        "PERMIT_PAYPAL_MERCHANT_ID", "PERMIT_PAYPAL_BASE_URL")


def run(*args, **env_overrides):
    env = {k: v for k, v in os.environ.items() if k not in KEYS}
    env.update(env_overrides)
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                          capture_output=True, text=True, timeout=120)


class SandboxRunTests(unittest.TestCase):
    def test_dry_run_passes_all_six_beats(self):
        with tempfile.TemporaryDirectory() as out:
            p = run("--dry-run", "--out", out, "--poll-interval", "0.05")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertIn("ledger chain: VERIFIED", p.stdout)
            [run_dir] = list(Path(out).iterdir())
            text = (run_dir / "evidence.md").read_text()
            self.assertIn("DRY RUN (mock rail). NOT sandbox evidence.", text)
            for n in range(1, 7):
                self.assertIn(f"## Beat {n}:", text)
            self.assertEqual(text.count("- Result: passed"), 6, text)
            self.assertNotIn("not reached", text)
            for name in ("events.jsonl", "ledger.json"):
                self.assertTrue((run_dir / name).is_file())

    def test_requires_explicit_mode(self):
        self.assertEqual(run().returncode, 2)
        self.assertEqual(run("--dry-run", "--sandbox").returncode, 2)

    def test_sandbox_refuses_without_keys(self):
        with tempfile.TemporaryDirectory() as out:
            p = run("--sandbox", "--out", out)
            self.assertEqual(p.returncode, 2)
            for k in KEYS[:3]:
                self.assertIn(f"{k} is not set", p.stderr)
            self.assertEqual(list(Path(out).iterdir()), [], "nothing may be written")

    def test_sandbox_refuses_partial_keys(self):
        p = run("--sandbox", PERMIT_PAYPAL_CLIENT_ID="x", PERMIT_PAYPAL_CLIENT_SECRET="y")
        self.assertEqual(p.returncode, 2)
        self.assertIn("PERMIT_PAYPAL_MERCHANT_ID is not set", p.stderr)

    def test_sandbox_refuses_live_host(self):
        p = run("--sandbox", PERMIT_PAYPAL_BASE_URL="https://api-m.paypal.com")
        self.assertEqual(p.returncode, 2)
        self.assertIn("live PayPal is refused", p.stderr)


if __name__ == "__main__":
    unittest.main()
