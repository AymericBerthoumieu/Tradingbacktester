from backtester import IntradayBacktesterApp
from intraday_strategies.all_strategies import INTRADY_STRATEGIES

symbols = ["aapl"]
strategy = INTRADY_STRATEGIES["Test"](symbols, qty=1)

backtester = IntradayBacktesterApp(cash=1000000)

backtester.load_data(symbols, "2023-04-01", "2023-04-8")

backtester.backtest(strategy)

print(backtester.orders)
print(backtester.inventory)
print(backtester.pnl)
print(backtester.limit_orders)
print(backtester.cash)
