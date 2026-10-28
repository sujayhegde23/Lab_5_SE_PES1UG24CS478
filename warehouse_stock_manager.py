"""Warehouse Stock Manager module.

Manages stock levels per SKU, checks reorder thresholds, persists inventory to
JSON files, and allows supervisor adjustments.
"""

import ast
from datetime import datetime
import hashlib
import hmac
import json
import operator
import os

# Global inventory storage
warehouse_stock: dict[str, int] = {}
AUDIT_FILE = "warehouse_audit.log"

# Allowed arithmetic operators for safe formula evaluation
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
}


def get_supervisor_auth_key() -> str:
    """Retrieve supervisor authentication key from environment or fallback."""
    return os.environ.get("WAREHOUSE_SUPERVISOR_KEY", "wh-admin-1234")


def safe_evaluate_formula(formula: str, current: int) -> int:
    """Safely evaluate arithmetic adjustment formulas without dynamic eval.

    Supports basic operations: current (+|-|*) non-negative integer.
    Rejects function calls, arbitrary attributes, and unsafe AST nodes.

    Args:
        formula: Arithmetic expression string (e.g. "current + 25").
        current: Current stock quantity as integer.

    Returns:
        Adjusted stock quantity as non-negative integer.

    Raises:
        ValueError: If expression syntax or node is unsupported or invalid.
    """
    if not isinstance(formula, str) or not formula.strip():
        raise ValueError("Formula must be a non-empty string.")

    try:
        tree = ast.parse(formula.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in formula: {exc}") from exc

    def _eval_node(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return int(node.value)
        if isinstance(node, ast.Name) and node.id == "current":
            return current
        if isinstance(node, ast.UnaryOp):
            val = _eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +val
            if isinstance(node.op, ast.USub):
                return -val
            op_name = type(node.op).__name__
            raise ValueError(f"Unsupported unary operator: {op_name}")
        if isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_func = _ALLOWED_OPERATORS.get(type(node.op))
            if op_func is None:
                op_name = type(node.op).__name__
                raise ValueError(f"Unsupported operator in formula: {op_name}")
            return int(op_func(left, right))
        node_name = type(node).__name__
        raise ValueError(f"Disallowed expression node in formula: {node_name}")

    result = _eval_node(tree)
    if result < 0:
        raise ValueError(
            f"Adjustment formula resulted in negative stock: {result}"
        )
    return result


def add_stock(
    sku: str = "default",
    qty: int = 0,
    history: list[str] | None = None,
) -> None:
    """Add received stock for a specified SKU."""
    if history is None:
        history = []
    if not isinstance(sku, str) or not sku.strip():
        raise TypeError("SKU must be a non-empty string.")
    if not isinstance(qty, int) or qty < 0:
        raise ValueError("Quantity to add must be a non-negative integer.")
    if qty == 0:
        return
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append(f"{datetime.now()}: Received {qty} units of {sku}")


def remove_stock(sku: str, qty: int) -> None:
    """Remove a specified quantity of stock for a given SKU."""
    if not isinstance(sku, str) or not sku.strip():
        raise TypeError("SKU must be a non-empty string.")
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("Quantity to remove must be a positive integer.")
    if sku not in warehouse_stock:
        raise KeyError(f"SKU '{sku}' not found in inventory.")
    if warehouse_stock[sku] < qty:
        avail = warehouse_stock[sku]
        raise ValueError(
            f"Cannot remove {qty} units from '{sku}'. Available: {avail}."
        )

    warehouse_stock[sku] -= qty
    if warehouse_stock[sku] == 0:
        del warehouse_stock[sku]


def get_stock(sku: str) -> int:
    """Return the current stock quantity for a SKU."""
    if sku not in warehouse_stock:
        raise KeyError(f"SKU '{sku}' not found in inventory.")
    return warehouse_stock[sku]


def sku_checksum(sku: str) -> str:
    """Generate a 6-character hex checksum for bin labels."""
    digest = hashlib.md5(
        sku.encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    return digest[:6]


def load_stock(file: str = "warehouse.json") -> None:
    """Load warehouse stock levels from a JSON file."""
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                warehouse_stock.clear()
                for key, val in data.items():
                    valid_key = isinstance(key, str)
                    valid_val = isinstance(val, int) and val >= 0
                    if valid_key and valid_val:
                        warehouse_stock[key] = val
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_stock(file: str = "warehouse.json") -> None:
    """Save warehouse stock levels to a JSON file."""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(warehouse_stock, f, indent=2)


def print_report() -> None:
    """Display a formatted warehouse stock inventory report."""
    print("Warehouse Stock Report")
    for s, qty in warehouse_stock.items():
        print(f"{s} -> {qty} units  [chk: {sku_checksum(str(s))}]")


def check_reorder(threshold: int = 10) -> list[str]:
    """Identify SKUs whose inventory is strictly below the threshold."""
    return [s for s, qty in warehouse_stock.items() if qty < threshold]


def apply_adjustment(sku: str, formula: str, auth_token: str) -> bool:
    """Apply a supervisor adjustment using safe formula evaluation.

    Args:
        sku: String SKU identifier.
        formula: Valid arithmetic expression string.
        auth_token: Supervisor authorization credential.

    Returns:
        True if adjustment succeeded, False if unauthorized.
    """
    expected_key = get_supervisor_auth_key()
    if not hmac.compare_digest(auth_token, expected_key):
        return False

    current = warehouse_stock.get(sku, 0)
    adjusted = safe_evaluate_formula(formula, current)
    warehouse_stock[sku] = adjusted
    timestamp = datetime.now()
    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write(
            f"adjusted {sku} using formula '{formula}' at {timestamp}\n"
        )
    return True


def main() -> None:
    """Demonstrate warehouse stock manager operations."""
    add_stock("WID-001", 40)
    try:
        add_stock("WID-002", -4)
    except ValueError as err:
        print(f"Rejected invalid quantity: {err}")
    add_stock("WID-002", 5)
    try:
        add_stock(404, 15)  # type: ignore
    except TypeError as err:
        print(f"Rejected invalid SKU type: {err}")
    remove_stock("WID-001", 12)
    try:
        remove_stock("GHOST-9", 1)
    except KeyError as err:
        print(f"Handled missing SKU: {err}")
    try:
        remove_stock("WID-001", 500)
    except ValueError as err:
        print(f"Handled overdraw attempt: {err}")
    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", check_reorder())
    adjustment_ok = apply_adjustment(
        "WID-002", "current + 25", "wh-admin-1234"
    )
    print("Adjustment applied successfully:", adjustment_ok)
    save_stock()
    load_stock()
    print_report()
    print("stock audit complete")


if __name__ == "__main__":
    main()
