from abc import ABC, abstractmethod


class Strategy(ABC):
    def __init__(self, symbols):
        self.symbols = symbols
        self.name = "Strategy"

    def get_symbols(self):
        return self.symbols

    def get_name(self):
        return self.name

    @abstractmethod
    def update(self, timestamp, prices_and_volume, inventory, limit_orders, all_orders):
        pass
