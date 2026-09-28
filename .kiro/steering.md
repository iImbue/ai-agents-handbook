# LedgerLite Steering Rules

1. **Acceptance Gate**: Every code modification MUST be verified by running python scripts/verify.py.
2. **Self-Correction**: If erify.py fails (Ruff linter or Pytest failures), analyze the stdout error logs, fix the code, and re-run erify.py until it prints VERIFY PASS.
3. **Architecture**: All core package code belongs in src/ledgerlite/ and all test coverage belongs in 	ests/.