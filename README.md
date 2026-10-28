# Lab 5: Static Code Analysis — Warehouse Stock Manager

**Student Name:** Sujay Hegde  
**SRN / Student ID:** PES1UG24CS478  
**Course:** Software Engineering (UE24CS352A / SE Lab)  
**Python Version:** Python 3.10+ (Tested on Python 3.11.9)

---

## 1. Project Overview

This repository contains the static code analysis, security auditing, refactoring, and regression testing for the **Warehouse Stock Manager** Python program. The system manages warehouse inventory per Stock Keeping Unit (SKU), supports receiving and removing stock, checks inventory thresholds for reordering, persists inventory to a JSON file, logs adjustment audits, and provides secure supervisor inventory adjustments.

The original program suffered from numerous code quality, style, security, and logic issues—including arbitrary dynamic code execution (`eval`), hardcoded credentials, mutable default arguments, bare exception catching, insecure hash usage, resource leaks from unclosed file handles, missing type/quantity validations, and lack of an import guard.

Through structured analysis using **Pylint**, **Bandit**, and **Flake8**, the program was methodically inspected, refactored, and verified.

---

## 2. Repository Structure

```text
Lab_5_SE_PES1UG24CS478/
├── .gitignore                         # Local artifacts & cache exclusions
├── README.md                          # Project documentation and guide
├── warehouse_stock_manager.py         # Refactored warehouse stock manager module
├── issues.md                          # Detailed table of documented issues and fixes
├── reflection.md                      # Lab reflection and responses
├── pylint_report_before.txt           # Pylint baseline analysis report (4.48/10)
├── bandit_report_before.txt           # Bandit baseline security analysis report
├── flake8_report_before.txt           # Flake8 baseline style analysis report
├── pylint_report_after.txt            # Pylint post-fix analysis report (10.00/10)
├── bandit_report_after.txt            # Bandit post-fix analysis report (0 issues)
├── flake8_report_after.txt            # Flake8 post-fix style report (0 violations)
└── tests/
    └── test_warehouse_stock_manager.py # Regression test suite using unittest
```

---

## 3. Environment Setup & Tool Installation

### Prerequisites
- Python 3.10 or newer (Python 3.11 recommended)
- Git

### Setup Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Required Static Analysis Tools
```bash
python -m pip install pylint bandit flake8
```

---

## 4. Execution Instructions

### Running the Program Demonstration
```bash
python warehouse_stock_manager.py
```

### Running the Regression Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Running Static Analysis Tools

**Pylint:**
```bash
python -m pylint warehouse_stock_manager.py
```

**Bandit (Security Linter):**
```bash
python -m bandit -r warehouse_stock_manager.py
```

**Flake8 (PEP 8 Style Checker):**
```bash
python -m flake8 warehouse_stock_manager.py
```

---

## 5. Summary of Analysis Reports & Scores

| Static Analysis Tool | Baseline (Before) | Cleaned Version (After) | Status |
|---|---|---|---|
| **Pylint** | `4.48 / 10` | `10.00 / 10` | **Passed** (>9.5 target) |
| **Bandit** | 5 issues (1 High, 2 Medium, 2 Low) | 0 issues | **Clean** |
| **Flake8** | 19 style & syntax violations | 0 violations | **Clean** |

Refer to [issues.md](issues.md) for full descriptions of all identified defects and their remediation approaches, and [reflection.md](reflection.md) for lab reflections.
