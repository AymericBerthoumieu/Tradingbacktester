from backtester import BacktestApp
from strategies.all_strategies import STRATEGIES
import matplotlib.pyplot as plt

# TODO: add logs


symbol = ["aapl", "BAC"]
start_date = "2021-01-01"
end_date = "2022-12-31"
strategy = "Long"

if __name__ == "__main__":
    # Create an instance of BacktestApp
    backtest_app = BacktestApp()

    backtest_app.load_data(symbol, start_date, end_date)

    backtest_app.set_strategy(STRATEGIES[strategy]())
    backtest_app.run_backtest()
    performance_metrics = backtest_app.performance_metrics

    print(performance_metrics)

    performance_metrics["Track record"].Index.plot()
    plt.show()
