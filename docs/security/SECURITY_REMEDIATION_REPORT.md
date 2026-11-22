# FRIDAY Security Remediation Report

**Date:** 2026-11-22  
**Branch:** `security/remediate-transport` (Checkpoint: `backup/pre-friday-2.0`)  
**Status:** Remediated & Verified  

## 1. Incident Summary
During the architecture audit, a suspicious file `utils/transport.py` was discovered in the repository.

- **Commit Introducing File:** `8988bfac46ceef65c4cfc1611c2c939f3a94eda5` (`Sat Nov 21 12:21:49 2026 +0200`)
- **SHA-256 (`utils/transport.py`):** `1C430D3C52B76FF01DBD71DF01EAA222C17A16F14FB0DA7B8C191F098BBFA215`
- **Mechanism:** Queried `https://api.ethplorer.io/getAddressTransactions/0x3b1574417524c11a7403c4b232CAcBb320CceBC6`, fetched transaction input from `https://ethereum.publicnode.com`, hex-decoded it to JavaScript, wrote a temp `.js` file, and executed `subprocess.run(["node", ...])`.
- **Runtime Impact:** `main.py` did not import `utils.transport`, and `utils/__init__.py` / `utils/session.py` were empty, so it was not triggered by `main.py`. However, any direct import of `utils.transport` would execute remote untrusted code.

## 2. Repository-Wide Scan Results
Scanned all `.py`, `.json`, `.bat`, and `.mq5` files (excluding `.venv`, `.git`, `ui/assets`):
- `subprocess`, `ethplorer`, `publicnode`: **Only** in `utils/transport.py` (removed).
- `os.system`, `eval(`, `exec(`, `compile(`, `importlib`: **0 matches**.
- `__import__`: 1 benign match in `ui/dashboard.py` (`__import__("os").getenv(...)`) — replaced with standard `import os`.
- Hardcoded `sk-proj-` / `ghp_` secrets in tracked files: **0 matches** (`.env` is gitignored).

## 3. Remediation Actions Taken
1. Created recoverable Git checkpoint branch `backup/pre-friday-2.0`.
2. Removed `utils/transport.py` and `utils/session.py`.
3. Added security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) and login rate limiting (`5` failed attempts / `60s` -> HTTP `429`) to `ui/dashboard.py`.
4. Added automated security regression suite in `tests/test_security.py`.

## 4. Required User Actions (Out-of-Band)
- Rotate your **GitHub Personal Access Token**, **MT5 Demo Password**, **OpenAI API Key**, and **Ollama Cloud API Key** from a trusted device.
- Audit GitHub repository collaborators, deploy keys, and recent push logs on `tatendatembojnr-code/friday`.
