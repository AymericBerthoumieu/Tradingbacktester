from intraday_strategies.strategy import Strategy
import pandas as pd


class TestStrategy(Strategy):
    def __init__(self, symbols, qty=1):
        Strategy.__init__(self, symbols)
        self.quantity = qty
        self.name = "Test Strategy"

    def update(self, timestamp, prices_and_volume, inventory, limit_orders, all_orders):
        new_limit_orders = pd.DataFrame(columns=limit_orders.columns)
        for s in self.symbols:
            if limit_orders[limit_orders.symbol == s].shape[0] == 0:
                if inventory[(inventory.symbol == s)]["inventory"].values[-1] > 0:
                    new_limit_orders = new_limit_orders.append(pd.Series([s,
                                                                          timestamp,
                                                                          "Sell",
                                                                          self.quantity,
                                                                          prices_and_volume.loc[timestamp]["High"] + 1],
                                                                         index=new_limit_orders.columns),
                                                               ignore_index=True)
                elif inventory[(inventory.symbol == s)]["inventory"].values[-1] < 0:
                    new_limit_orders = new_limit_orders.append(pd.Series([s,
                                                                          timestamp,
                                                                          "Buy",
                                                                          self.quantity,
                                                                          prices_and_volume.loc[timestamp]["Low"] - 1],
                                                                         index=new_limit_orders.columns),
                                                               ignore_index=True)
                else:
                    new_limit_orders = new_limit_orders.append(pd.Series([s,
                                                                          timestamp,
                                                                          "Buy",
                                                                          self.quantity,
                                                                          prices_and_volume.loc[timestamp]["Low"] - 1],
                                                                         index=new_limit_orders.columns),
                                                               ignore_index=True)

                    new_limit_orders = new_limit_orders.append(pd.Series([s,
                                                                          timestamp,
                                                                          "Short-Sell",
                                                                          self.quantity,
                                                                          prices_and_volume.loc[timestamp]["High"] + 1],
                                                                         index=new_limit_orders.columns),
                                                               ignore_index=True)
        return new_limit_orders
