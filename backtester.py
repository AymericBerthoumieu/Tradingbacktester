import yfinance as yf
import quandl
import pandas as pd
import pandas_datareader as pdr
import numpy as np
from tqdm import tqdm
import datetime as dt


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
        performance_metrics['Win Rate'] = performance_metrics['Winning Days'] / (
                    performance_metrics['Winning Days'] + performance_metrics['Losing Days'])
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
                drawdown = (cum_return[i] - peak) / peak
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


class IntradayBacktesterApp:
    def __init__(self, cash):
        self.data = None
        self.orders = pd.DataFrame(columns=["symbol", "timestamp", "action", "quantity", "price"])
        self.inventory = pd.DataFrame(columns=["symbol", "timestamp", "inventory"])
        self.pnl = pd.DataFrame(columns=["timestamp", "pnl"])
        self.limit_orders = None
        self.cash = cash

    def load_data(self, symbol, start_date, end_date):
        current_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")

        if current_date + dt.timedelta(days=7) > end_date:
            self.data = yf.download(symbol, start=current_date, end=end_date, interval="1m")
        else:
            while current_date + dt.timedelta(days=7) < end_date:
                if self.data is None:
                    self.data = yf.download(symbol, start=current_date, end=current_date + dt.timedelta(days=7), interval="1m")
                else:
                    new_data = yf.download(symbol, start=current_date, end=current_date + dt.timedelta(days=7), interval="1m")
                    self.data = pd.concat(self.data, new_data)

    def execute_order(self, symbol, timestamp, action, quantity, price=None):
        """Execute an order and update orders, inventory, and profit/loss"""
        self.orders = self.orders.append(
            pd.Series([symbol, timestamp, action, quantity, price], index=self.orders.columns), ignore_index=True)

        try:
            inventory_qty = self.inventory.loc[(self.inventory["symbol"] == symbol)]["inventory"].values[-1]
        except:
            inventory_qty = 0

        valid_actions = ["Buy", "Sell", "Short-Sell"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action '{action}', must be one of {valid_actions}")

        if (price is None) or self.data.loc[timestamp, "Low"] <= price <= self.data.loc[timestamp, "High"]:
            if action == "Sell" and (symbol not in self.inventory["symbol"].values):
                raise ValueError(f"No inventory for symbol '{symbol}' to execute '{action}' order")
            else:
                if action == "Buy":
                    self.inventory = self.inventory.append(pd.Series([symbol, timestamp, inventory_qty+quantity], index=self.inventory.columns), ignore_index=True)
                    self.cash -= quantity * (self.data.loc[timestamp, "Low"] + self.data.loc[timestamp, "High"]) / 2
                elif action == "Sell":
                    if inventory_qty < quantity:
                        raise ValueError(f"Insufficient inventory for selling {quantity} shares of {symbol}")
                    else:
                        self.inventory = self.inventory.append(pd.Series([symbol, timestamp, inventory_qty - quantity], index=self.inventory.columns), ignore_index=True)
                        self.cash += quantity * (self.data.loc[timestamp, "Low"] + self.data.loc[timestamp, "High"]) / 2
                elif action == "Short-Sell":
                    self.inventory = self.inventory.append(pd.Series([symbol, timestamp, inventory_qty - quantity], index=self.inventory.columns), ignore_index=True)
                    self.cash += quantity * (self.data.loc[timestamp, "Low"] + self.data.loc[timestamp, "High"]) / 2
        else:
            # keep limit order
            self.limit_orders = self.limit_orders.append(
                pd.Series([symbol, timestamp, action, quantity, price], index=self.limit_orders.columns),
                ignore_index=True)

        self.update_pnl()

    def backtest(self, strategy):
        """Backtest the given strategy"""
        if self.data is None:
            raise ValueError("No data loaded. Please load data before backtesting.")

        for index, prices in tqdm(self.data.iterrows()):
            orders = strategy.update(index, data, self.inventory, self.limit_orders)
            for order in orders:
                self.execute_order(order["symbol"], index, order["action"], order["quantity"], prices["Close"])

    def get_orders(self):
        """Get the list of executed orders"""
        return self.orders

    def get_inventory(self):
        """Get the inventory of the trading strategy over time"""
        return self.inventory

    def get_profit_loss(self):
        """Get the profit/loss of the trading strategy over time"""
        return self.pnl

    def update_pnl(self):
        # TODO: compute unrealised pnl over time
        pass
