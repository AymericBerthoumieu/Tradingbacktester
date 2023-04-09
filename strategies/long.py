from strategies.strategy import Strategy
import pandas as pd


class Long(Strategy):

    def apply_strategy(self, symbols, data):
        self.symbols = symbols
        if len(symbols) == 1:
            self.data = data["Adj Close"].rename(columns={'Adj Close': symbols[0].upper()})
        else:
            self.data = data[[("Adj Close", x.upper()) for x in self.symbols]].droplevel(0, axis=1)

        self.compute_weights(symbols, data.index)
        self.compute_track_record()

        return self.track_record

    def compute_weights(self, symbols, dates):
        self.weights = pd.DataFrame(index=dates, columns=[x.upper() for x in symbols]).fillna(1 / len(symbols))

    def compute_track_record(self):
        returns = self.data.pct_change()
        self.track_record = (returns * self.weights).sum(axis=1).fillna(0).to_frame("Return")
        self.track_record["Cumulative Return"] = self.track_record["Return"].add(1).cumprod()
        self.track_record["Index"] = self.init_value * self.track_record["Cumulative Return"]
