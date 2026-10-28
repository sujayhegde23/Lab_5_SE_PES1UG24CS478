"""Unit and regression tests for warehouse_stock_manager module."""

import json
import os
import tempfile
import unittest

import warehouse_stock_manager as wsm


class TestWarehouseStockManager(unittest.TestCase):
    """Test suite verifying warehouse stock manager behavior."""

    def setUp(self) -> None:
        """Reset warehouse stock dictionary before each test."""
        wsm.warehouse_stock.clear()

    def tearDown(self) -> None:
        """Clean up warehouse stock after each test."""
        wsm.warehouse_stock.clear()

    def test_add_stock_valid(self) -> None:
        """Test receiving stock increases SKU quantity."""
        wsm.add_stock("SKU-100", 25)
        self.assertEqual(wsm.get_stock("SKU-100"), 25)
        wsm.add_stock("SKU-100", 15)
        self.assertEqual(wsm.get_stock("SKU-100"), 40)

    def test_add_stock_invalid_sku(self) -> None:
        """Test invalid SKU types are rejected with TypeError."""
        with self.assertRaises(TypeError):
            wsm.add_stock(12345, 10)  # type: ignore
        with self.assertRaises(TypeError):
            wsm.add_stock("", 10)

    def test_add_stock_invalid_qty(self) -> None:
        """Test negative or non-integer quantities are rejected with ValueError."""
        with self.assertRaises(ValueError):
            wsm.add_stock("SKU-101", -5)

    def test_add_stock_mutable_default_isolation(self) -> None:
        """Test that default history list is not shared across calls."""
        wsm.add_stock("SKU-A", 10)
        wsm.add_stock("SKU-B", 20)
        custom_history: list[str] = []
        wsm.add_stock("SKU-C", 30, history=custom_history)
        self.assertEqual(len(custom_history), 1)

    def test_remove_stock_valid(self) -> None:
        """Test removing valid stock decreases quantity."""
        wsm.add_stock("SKU-200", 50)
        wsm.remove_stock("SKU-200", 20)
        self.assertEqual(wsm.get_stock("SKU-200"), 30)

    def test_remove_stock_to_zero(self) -> None:
        """Test removing exact remaining quantity removes SKU from active stock."""
        wsm.add_stock("SKU-201", 15)
        wsm.remove_stock("SKU-201", 15)
        with self.assertRaises(KeyError):
            wsm.get_stock("SKU-201")

    def test_remove_stock_nonexistent_sku(self) -> None:
        """Test removing stock from unknown SKU raises KeyError."""
        with self.assertRaises(KeyError):
            wsm.remove_stock("NONEXISTENT", 5)

    def test_remove_stock_overdraw(self) -> None:
        """Test requesting more stock than available raises ValueError."""
        wsm.add_stock("SKU-202", 10)
        with self.assertRaises(ValueError):
            wsm.remove_stock("SKU-202", 50)
        # Verify stock remains untouched after failed overdraw
        self.assertEqual(wsm.get_stock("SKU-202"), 10)

    def test_sku_checksum(self) -> None:
        """Test SKU checksum returns a 6-character hex string."""
        chk = wsm.sku_checksum("WID-001")
        self.assertIsInstance(chk, str)
        self.assertEqual(len(chk), 6)

    def test_check_reorder(self) -> None:
        """Test reorder threshold correctly identifies low-stock items."""
        wsm.add_stock("ITEM-A", 5)
        wsm.add_stock("ITEM-B", 15)
        wsm.add_stock("ITEM-C", 9)
        reorders = wsm.check_reorder(threshold=10)
        self.assertIn("ITEM-A", reorders)
        self.assertIn("ITEM-C", reorders)
        self.assertNotIn("ITEM-B", reorders)

    def test_save_and_load_stock(self) -> None:
        """Test saving inventory to JSON and reloading preserves data."""
        wsm.add_stock("ITEM-SAVE", 42)
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name

        try:
            wsm.save_stock(file=tmp_path)
            wsm.warehouse_stock.clear()
            self.assertEqual(len(wsm.warehouse_stock), 0)
            wsm.load_stock(file=tmp_path)
            self.assertEqual(wsm.get_stock("ITEM-SAVE"), 42)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_load_stock_missing_file_preserves_stock(self) -> None:
        """Test loading from a nonexistent file does not crash or erase stock."""
        wsm.add_stock("ITEM-KEEP", 99)
        wsm.load_stock("non_existent_file_xyz123.json")
        self.assertEqual(wsm.get_stock("ITEM-KEEP"), 99)


if __name__ == "__main__":
    unittest.main()
