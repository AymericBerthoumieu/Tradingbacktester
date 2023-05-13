from Backtesters.backtester import IntradayBacktesterApp
from intraday_strategies.all_strategies import INTRADY_STRATEGIES

symbols = ["aapl"]
strategy = INTRADY_STRATEGIES["Test"](symbols, qty=1)

backtester = IntradayBacktesterApp(cash=1000000)

backtester.load_data(symbols, "2023-05-01", "2023-05-03")

backtester.backtest(strategy)

print(backtester.orderHistory)
print(backtester.inventory)
print(backtester.book_value)
print(backtester.outstanding_limit_orders)
print(backtester.cash)
