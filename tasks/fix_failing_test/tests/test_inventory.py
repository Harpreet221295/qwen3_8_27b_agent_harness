import pytest
from inventory import Inventory


def test_add_accumulates():
    inv = Inventory(); inv.add("apple", 3, 0.5); inv.add("apple", 2, 0.5)
    assert inv.items["apple"]["qty"] == 5


def test_add_rejects_nonpositive():
    inv = Inventory()
    with pytest.raises(ValueError): inv.add("x", 0, 1.0)


def test_remove_and_delete():
    inv = Inventory(); inv.add("pear", 2, 1.0); inv.remove("pear", 2)
    assert "pear" not in inv.items


def test_total_value():
    inv = Inventory(); inv.add("a", 2, 1.5); inv.add("b", 1, 10.0)
    assert inv.total_value() == 13.0


def test_low_stock():
    inv = Inventory(); inv.add("a", 2, 1); inv.add("b", 9, 1); inv.add("c", 5, 1)
    assert inv.low_stock() == ["a"]
    assert inv.low_stock(threshold=9) == ["a", "c"]
