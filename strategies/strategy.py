from abc import ABC, abstractmethod


class Strategy(ABC):

    def __init__(self):
        self.init_value = 1000
        self.weigths = None
        self.data = None
        self.symbols = None
        self.track_record = None

    @abstractmethod
    def apply_strategy(self, symbols, data):
        return
