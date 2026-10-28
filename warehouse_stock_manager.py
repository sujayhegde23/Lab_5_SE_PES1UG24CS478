"""Warehouse Stock Manager module.

Manages stock levels per SKU, checks reorder thresholds, persists inventory to
JSON files, and allows supervisor adjustments.
"""

from datetime import datetime
import hashlib
import json

# Global inventory storage
warehouse_stock: dict[str, int] = {}
AUDIT_FILE = "warehouse_audit.log"
SUPERVISOR_PASSWORD = "wh-admin-1234"


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
        raise ValueError(
            f"Cannot remove {qty} units from '{sku}'. Available: {warehouse_stock[sku]}."
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
    return hashlib.md5(sku.encode("utf-8")).hexdigest()[:6]


def load_stock(file: str = "warehouse.json") -> None:
    """Load warehouse stock levels from a JSON file."""
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                warehouse_stock.clear()
                for key, val in data.items():
                    if isinstance(key, str) and isinstance(val, int) and val >= 0:
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


def apply_adjustment(sku: str, formula: str, password: str) -> None:
    """Apply a supervisor adjustment using an expression."""
    if password != SUPERVISOR_PASSWORD:
        return
    current = warehouse_stock.get(sku, 0)
    warehouse_stock[sku] = eval(formula, {"current": current})
    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write(f"adjusted {sku} using formula {formula} at {datetime.now()}\n")


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
    apply_adjustment("WID-002", "current + 25", "wh-admin-1234")
    save_stock()
    load_stock()
    print_report()
    eval("print('stock audit complete')")


if __name__ == "__main__":
    main()
