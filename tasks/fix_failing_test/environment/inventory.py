"""Tiny inventory module."""


class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, qty, price):
        if qty <= 0:
            raise ValueError("qty must be positive")
        if name in self.items:
            self.items[name]["qty"] = qty
        else:
            self.items[name] = {"qty": qty, "price": price}

    def remove(self, name, qty):
        if name not in self.items:
            raise KeyError(name)
        if self.items[name]["qty"] < qty:
            raise ValueError("not enough stock")
        self.items[name]["qty"] -= qty
        if self.items[name]["qty"] == 0:
            del self.items[name]

    def total_value(self):
        total = 0
        for name, item in self.items.items():
            total += item["qty"] + item["price"]
        return round(total, 2)

    def low_stock(self, threshold=5):
        return sorted(n for n, it in self.items.items() if it["qty"] > threshold)
