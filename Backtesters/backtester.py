import yfinance as yf
import quandl
import pandas as pd
import pandas_datareader as pdr
import numpy as np
from tqdm import tqdm
import datetime as dt
from utils.report import ReportGenerator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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
    # For now only one symbol by one symbol
    def __init__(self, cash):
        self.data = None
        self.orderHistory = pd.DataFrame(columns=["symbol", "timestamp", "side", "quantity", "price"])
        self.executed_orders = pd.DataFrame(columns=["symbol", "timestamp", "side", "quantity", "price", "market"])
        self.inventory = pd.DataFrame(columns=["symbol", "timestamp", "inventory"])
        self.inventory.set_index("timestamp", inplace=True)
        self.book_value = pd.DataFrame(columns=["timestamp", "value"])
        self.outstanding_limit_orders = pd.DataFrame(columns=["symbol", "timestamp", "side", "quantity", "price"])
        self.cash = cash

    def load_data(self, symbol, start_date, end_date):
        # TODO: find good data provider. This might induce change in the code bellow in name of columns.
        current_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")

        if current_date + dt.timedelta(days=7) > end_date:
            self.data = yf.download(symbol, start=current_date, end=end_date, interval="1m")
        else:
            while current_date + dt.timedelta(days=7) < end_date:
                if self.data is None:
                    self.data = yf.download(symbol, start=current_date, end=current_date + dt.timedelta(days=7),
                                            interval="1m")
                else:
                    new_data = yf.download(symbol, start=current_date, end=current_date + dt.timedelta(days=7),
                                           interval="1m")
                    self.data = pd.concat((self.data, new_data))
                current_date = current_date + dt.timedelta(days=8)
            if current_date < end_date:
                new_data = yf.download(symbol, start=current_date, end=end_date, interval="1m")
                self.data = pd.concat((self.data, new_data))

        if len(symbol) > 1:
            self.data = self.data.stack().reset_index(level=1).rename({"level_1": "symbol"}, axis=1)
        else:
            self.data["symbol"] = symbol[0]

    def set_data(self, data):
        """To input external data"""
        self.data = data

    def execute_order(self, symbol, timestamp, side, quantity, price=None):
        """Execute an order and update orders, inventory, and profit/loss"""
        self.orderHistory = self.orderHistory.append(
            pd.Series([symbol, timestamp, side, quantity, price], index=self.orderHistory.columns), ignore_index=True)

        inventory_qty = self.inventory[self.inventory["symbol"] == symbol].loc[:timestamp, "inventory"].values[0]

        valid_actions = ["Buy", "Sell", "Short-Sell"]
        if side not in valid_actions:
            raise ValueError(f"Invalid side '{side}', must be one of {valid_actions}")

        if (price is None) or self.data[self.data.symbol == symbol].loc[timestamp, "Low"] <= price <= self.data[self.data.symbol == symbol].loc[timestamp, "High"]:

            # What could go wrong
            if symbol not in self.inventory["symbol"].values:
                raise ValueError(f"No inventory for symbol '{symbol}' to execute '{side}' order")
            elif side == "Sell" and inventory_qty < quantity:
                raise ValueError(f"Insufficient inventory for selling {quantity} shares of {symbol}")

            else:
                exec_price = ((self.data[self.data.symbol == symbol].loc[timestamp, "Low"] + self.data[self.data.symbol == symbol].loc[timestamp, "High"]) / 2) if (price is None) else price
                self.executed_orders = self.executed_orders.append(pd.Series([symbol, timestamp, side, quantity, exec_price, price is None], index=self.executed_orders.columns), ignore_index=True)
                self.inventory = self.inventory.append(pd.DataFrame([[symbol, inventory_qty + (2*(side == "Buy")-1) * quantity]], index=[timestamp], columns=self.inventory.columns), ignore_index=False)
                self.cash = self.cash + (2*(side != "Buy")-1) * quantity * exec_price
        else:
            # keep limit order
            self.outstanding_limit_orders = self.outstanding_limit_orders.append(pd.Series([symbol, timestamp, side, quantity, price], index=self.outstanding_limit_orders.columns), ignore_index=True)

    def backtest(self, strategy):
        """Backtest the given strategy"""
        if self.data is None:
            raise ValueError("No data loaded. Please load data before backtesting.")

        self.initialize(strategy)

        for index, prices in tqdm(self.data.iloc[1:].iterrows(), desc="Running strategy: ", ncols=100, total=self.data.shape[0]-1):
            # at period T I can only take decision using data at end of period T-1, hence the shift
            orders = strategy.update(index, self.data.shift(1), self.inventory, self.outstanding_limit_orders, self.orderHistory)
            orders = pd.concat((self.outstanding_limit_orders, orders))
            self.outstanding_limit_orders = pd.DataFrame(columns=["symbol", "timestamp", "side", "quantity", "price"])

            # Execute orders
            for _, order in orders.iterrows():
                self.execute_order(order["symbol"], index, order["side"], order["quantity"], order["price"])

            # Update inventory
            if not index in self.inventory.index:
                for s in strategy.get_symbols():
                    inventory_qty = self.inventory[self.inventory["symbol"] == s].loc[:index, "inventory"].values[0]
                    self.inventory = self.inventory.append(pd.DataFrame([[s, inventory_qty]], index=[index], columns=self.inventory.columns), ignore_index=False)
            else:
                for s in strategy.get_symbols():
                    if not s in self.inventory.loc[index].symbol:
                        inventory_qty = self.inventory[self.inventory["symbol"] == s].loc[:index, "inventory"].values[0]
                        self.inventory = self.inventory.append(pd.DataFrame([[s, inventory_qty]], index=[index], columns=self.inventory.columns), ignore_index=False)

            self.update_book_value(index)

        self.generate_report(strategy.get_name())

    def get_orders(self):
        """Get the list of executed orders"""
        return self.orderHistory

    def get_inventory(self):
        """Get the inventory of the trading strategy over time"""
        return self.inventory

    def get_profit_loss(self):
        """Get the profit/loss of the trading strategy over time"""
        return self.book_value

    def initialize(self, strat):
        """
        :param strat:
        :return:
        """
        symbols = strat.get_symbols()
        min_time = self.data.index[0]
        for s in symbols:
            self.inventory = self.inventory.append(pd.DataFrame([[s, 0]], index=[min_time], columns=self.inventory.columns), ignore_index=False)

    def update_book_value(self, timestamp):
        """
        :param timestamp:
        :return:
        """
        current_value = self.cash
        for s in self.inventory.symbol.unique():
            qty = self.inventory[self.inventory.symbol == s].loc[timestamp, "inventory"]
            price = (self.data[self.data.symbol == s].loc[timestamp, "High"] + self.data[self.data.symbol == s].loc[timestamp, "Low"]) / 2
            current_value += qty * price
        self.book_value = self.book_value.append(pd.Series([timestamp, current_value], index=self.book_value.columns), ignore_index=True)

    def add_summary_info(self, report, strat_name):
        report.add_text("")
        report.add_text("Strategy: " + strat_name)
        report.add_text("From: " + self.data.index.min().strftime("%Y-%m-%d %H:%M:%S"))
        report.add_text("To: " + self.data.index.max().strftime("%Y-%m-%d %H:%M:%S"))
        report.add_text("Universe: " + ", ".join(self.data.symbol.unique()))
        report.add_text("Final Value: " + str(self.book_value.value.values[-1]))
        return report

    @staticmethod
    def add_break(report):
        report.add_text("")
        report.add_text("")
        report.add_text("")
        return report

    def plot_book_value(self, report):
        fig = plt.figure(figsize=(15, 5))
        plt.plot(self.book_value.timestamp.values, self.book_value.value.values)
        plt.title("Book value (cash + MtM of inventory) over time")
        report.add_chart("Book value (cash + MtM of inventory) over time", fig)
        return report

    def generate_report(self, strat_name):
        report_generator = ReportGenerator("reports/" + strat_name.replace(" ", "_") + "_" + dt.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".html")

        report_generator.add_title("Intra-Day Strategy Report")
        report_generator = self.add_summary_info(report_generator, strat_name)
        report_generator = self.add_break(report_generator)
        report_generator = self.plot_book_value(report_generator)

        report_generator.generate_report()
