from backtester import IntradayBacktesterApp
from intraday_strategies.all_strategies import INTRADY_STRATEGIES

symbols = ["aapl"]
strategy = INTRADY_STRATEGIES["Test"](symbols, qty=1)

backtester = IntradayBacktesterApp(cash=1000000)

backtester.load_data(symbols, "2023-04-12", "2023-04-22")

backtester.backtest(strategy)

print(backtester.orderHistory)
print(backtester.inventory)
print(backtester.pnl)
print(backtester.outstanding_limit_orders)
print(backtester.cash)
