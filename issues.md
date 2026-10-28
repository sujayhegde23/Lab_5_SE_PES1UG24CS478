# Static Code Analysis Issues — Warehouse Stock Manager

## 1. Overview of Identified Issues

The original `warehouse_stock_manager.py` was analyzed using **Pylint**, **Bandit**, and **Flake8**, supplemented by manual code review for runtime logic and correctness defects. The table below documents the identified issues, their categories, baseline line numbers, descriptions, and remediation approaches.

---

## 2. Issue Findings Table

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| **Arbitrary Dynamic Code Execution (`eval`)** | Security (Bandit B307, Pylint W0123) | 62, 80 | `applyAdjustment()` uses Python's built-in `eval()` on an untrusted formula string, allowing arbitrary code execution (CWE-78/CWE-95). Line 80 additionally calls `eval("print('stock audit complete')")` unnecessarily. | Remove `eval()` entirely. Replace line 80 with standard `print()`. In `apply_adjustment()`, replace raw evaluation with a safe, tokenized math evaluator supporting strictly allowed operations (`+`, `-`, `*`) on non-negative numeric operands without dynamic code execution. |
| **Hard-Coded Supervisor Password** | Security (Bandit B105) | 10 | `SUPERVISOR_PASSWORD = "wh-admin-1234"` embeds plaintext administrative credentials directly in the source code (CWE-259), exposing authentication secrets to any user with repository access. | Replace the hardcoded password constant with retrieval from an environment variable (e.g. `os.environ.get("SUPERVISOR_PASSWORD")`) or provide a secure default fallback for test/demo environments while hashing password comparisons via constant-time comparison (`hmac.compare_digest`). |
| **Insecure Cryptographic Hash Usage (MD5)** | Security (Bandit B324) | 31 | `hashlib.md5(sku.encode()).hexdigest()[:6]` uses MD5 without indicating non-security context, triggering Bandit warning for weak hash algorithms (CWE-327). | Specify `usedforsecurity=False` in `hashlib.md5(sku.encode(), usedforsecurity=False)` to explicitly document that the 6-character digest is only used as a non-cryptographic bin label fingerprint. |
| **Silent Exception Suppression via Bare Except** | Correctness / Security (Bandit B110, Pylint W0702, Flake8 E722) | 23–24 | `removeStock()` catches all exceptions with a bare `except: pass`, masking programming bugs, `KeyError` on nonexistent SKUs, and `TypeError` without notification or recovery. | Eliminate the bare `except: pass`. Explicitly validate whether the SKU exists in stock and check whether sufficient quantity is available before deducting. Raise specific exceptions (`KeyError`, `ValueError`) or return explicit status booleans. |
| **Mutable Default Argument (`history=[]`)** | Bug / Correctness (Pylint W0102) | 12 | `def addStock(sku="default", qty=0, history=[])` uses a mutable empty list as default argument. In Python, default lists are instantiated once at function definition, causing state to leak across independent invocations. | Change the parameter default to `None` (`history=None`) and initialize a new list inside the function body (`history = [] if history is None else history`). |
| **Unclosed Files & Missing Context Managers** | Maintainability / Bug (Pylint R1732, W1514) | 34, 40, 63 | `loadStock()`, `saveStock()`, and `applyAdjustment()` open files using raw `open()` without a `with` statement and without specifying text encoding, risking file descriptor leaks on exceptions and platform encoding discrepancies. | Use context managers (`with open(file, "r", encoding="utf-8") as f:`) across all file read/write operations to guarantee deterministic file closure and UTF-8 encoding. |
| **Missing Input Validation (SKU Type & Negative Quantities)** | Logic / Correctness (Manual Review) | 12–16, 18–22, 69 | `addStock()` and `removeStock()` accept negative quantities and non-string SKUs (e.g., integer `404` or negative qty `-4`), corrupting stock levels and creating negative inventory without error. | Validate that `sku` is a non-empty string and `qty` is an integer strictly greater than zero (`qty > 0`). Raise `TypeError` or `ValueError` when invalid arguments are provided. |
| **Inventory Overdraw Handling** | Logic / Correctness (Manual Review) | 20–22, 72 | In `removeStock()`, removing more units than available (e.g., removing 500 units from 28) results in a negative intermediate value and triggers `del warehouse_stock[sku]`, silently erasing stock without overdraft protection. | Check that `warehouse_stock[sku] >= qty`. If requested quantity exceeds current stock, raise `ValueError` stating insufficient inventory. If stock reaches exactly zero, set to 0 or delete deterministically according to inventory policy. |
| **Unused Imports & Variables** | Code Quality (Pylint W0611, W0612, Flake8 F401, F841) | 2, 4, 54 | `logging` and `os` are imported but never used. In `checkReorder()`, `total_units = sum(warehouse_stock.values())` computes the sum but is never referenced or returned. | Remove dead imports (`logging`, `os` if unneeded, or use `os` for secure password env lookup). Remove unused variable `total_units` or include it in meaningful warehouse statistics reporting. |
| **PEP 8 Formatting & Inconsistent Naming** | Style / Maintainability (Pylint C0103, Flake8 E302, E305, E501, W291) | Multiple lines | Functions use camelCase (`addStock`, `removeStock`, etc.) instead of snake_case (`add_stock`, `remove_stock`). Global statements and missing docstrings reduce maintainability. Lines exceed maximum length. | Rename functions to snake_case (`add_stock`, `remove_stock`, `get_stock`, `sku_checksum`, `load_stock`, `save_stock`, `print_report`, `check_reorder`, `apply_adjustment`). Add descriptive module and function docstrings. Enforce PEP 8 blank line rules and line lengths. |
| **Top-Level Execution Without Main Guard** | Maintainability / Design (Manual Review) | 82 | `main()` is executed unconditionally at the root of the script, causing the demo to run whenever the module is imported in test suites or external modules. | Guard the demonstration execution inside `if __name__ == "__main__": main()`. |

---

## 3. Prioritization Strategy

1. **Security Fixes (High Priority):**
   - Eliminate `eval()` and replace formula adjustments with a safe, bounded parser.
   - Remove plaintext password vulnerability and use environment lookup with constant-time verification.
   - Fix MD5 usage flag (`usedforsecurity=False`).
2. **Correctness & Robustness (Medium to High Priority):**
   - Replace bare `except: pass` with explicit precondition checks and proper exception raising.
   - Fix mutable default argument `history=[]`.
   - Implement strict SKU and quantity validation to prevent invalid/negative inventory.
   - Prevent inventory overdraws.
   - Guard file operations with `with` blocks and specified encoding.
3. **Style & Code Quality (Target Pylint > 9.5, Flake8 0 violations):**
   - Adopt PEP 8 snake_case naming conventions and type hints.
   - Add comprehensive docstrings for module and functions.
   - Remove unused imports and variables.
   - Add standard `if __name__ == "__main__":` entry point.
