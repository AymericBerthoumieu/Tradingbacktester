import yfinance as yf
import quandl
import pandas_datareader as pdr
import numpy as np


class BacktestApp:
    def __init__(self, data_provider='yfinance'):
        self.data_provider = data_provider
        self.data = None
        self.strategy = None
        self.track_record = None
        self.performance_metrics = None
        self.root = None
        self.symbols = None

    def load_data(self, symbol, start_date, end_date):
        self.symbols = symbol

        if self.data_provider == 'yfinance':
            # TODO: set strategy type to intra-day or not and get data with 1 minute interval when needed
            self.data = yf.download(symbol, start=start_date, end=end_date)
        elif self.data_provider == 'pandas_datareader':
            self.data = pdr.get_data_yahoo(symbol, start=start_date, end=end_date)
        elif self.data_provider == 'quandl':
            api_key = 'YOUR_QUANDL_API_KEY'
            quandl.ApiConfig.api_key = api_key
            self.data = quandl.get(f"WIKI/{symbol}", start_date=start_date, end_date=end_date)
        else:
            raise ValueError(
                "Invalid data provider. Please choose from 'yfinance', 'pandas_datareader', or 'quandl'.")

        print(self.data)

    def set_strategy(self, strategy):
        self.strategy = strategy

    def run_backtest(self):
        if self.data is None:
            raise ValueError("Data has not been loaded. Please load data using 'load_data()' method.")
        if self.strategy is None:
            raise ValueError("Strategy has not been set. Please set strategy using 'set_strategy()' method.")

        self.track_record = self.strategy.apply_strategy(self.symbols, self.data)
        self.performance_metrics = self.calculate_performance_metrics()

    def calculate_performance_metrics(self):
        if self.track_record is None:
            raise ValueError("Track record is empty. Please run backtest using 'run_backtest()' method.")

        performance_metrics = {}
        performance_metrics['Track record'] = self.track_record
        performance_metrics['Winning Days'] = sum(self.track_record['Return'] > 0)
        performance_metrics['Losing Days'] = sum(self.track_record['Return'] < 0)
        performance_metrics['Win Rate'] = performance_metrics['Winning Days'] / (performance_metrics['Winning Days'] + performance_metrics['Losing Days'])
        performance_metrics['Average return'] = np.mean(self.track_record['Return'])
        performance_metrics['Max Drawdown'] = self.calculate_max_drawdown(self.track_record)
        performance_metrics['Sharpe Ratio'] = self.calculate_sharpe_ratio(self.track_record)
        # Add more performance metrics as needed

        return performance_metrics

    @staticmethod
    def calculate_max_drawdown(track_record):
        cum_return = track_record["Index"]
        peak = cum_return[0]
        max_drawdown = 0
        for i in range(1, len(cum_return)):
            if cum_return[i] > peak:
                peak = cum_return[i]
                drawdown = 0
            else:
                drawdown = (cum_return[i] - peak)/peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown
        return max_drawdown

    @staticmethod
    def calculate_sharpe_ratio(track_record, risk_free_rate=0.0):
        """
        Calculates the Sharpe ratio from a track record of returns.

        Parameters:
            - track_record (array-like): Array or list of historical returns.
            - risk_free_rate (float): Risk-free rate, default is 0.0.

        Returns:
            - float: Sharpe ratio.
        """
        track_record = np.array(track_record.Return)
        excess_returns = track_record - risk_free_rate
        std_dev = np.std(track_record)
        sharpe_ratio = np.mean(excess_returns) / std_dev
        return sharpe_ratio
