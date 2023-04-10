from abc import ABC, abstractmethod


class Strategy(ABC):
    def __init__(self, symbols):
        self.symbols = symbols

    @abstractmethod
    def update(self, timestamp, prices_and_volume, inventory, limit_orders):
        pass
