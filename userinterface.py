import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from backtester import BacktestApp
from strategies.all_strategies import STRATEGIES

# Create an instance of BacktestApp
backtest_app = BacktestApp()


# Function to load data from user input
def load_data():
    try:
        symbol = symbol_entry.get().split(",")
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()
        backtest_app.load_data(symbol, start_date, end_date)
        messagebox.showinfo("Info", "Data loaded successfully.")
    except:
        messagebox.showinfo("Error", "Error while loading data.")


# Function to run backtest
def run_backtest():
    strategy = strategy_combobox.get()
    backtest_app.set_strategy(STRATEGIES[strategy]())
    backtest_app.run_backtest()
    performance_metrics = backtest_app.performance_metrics



# Create main window
root = tk.Tk()
root.title("Backtester")
root.geometry("300x200")

# Create widgets
symbol_label = ttk.Label(root, text="Symbol:")
symbol_label.pack()
symbol_entry = ttk.Entry(root)
symbol_entry.pack()

start_date_label = ttk.Label(root, text="Start Date:")
start_date_label.pack()
start_date_entry = ttk.Entry(root)
start_date_entry.pack()

end_date_label = ttk.Label(root, text="End Date:")
end_date_label.pack()
end_date_entry = ttk.Entry(root)
end_date_entry.pack()

strategy_label = ttk.Label(root, text="Strategy:")
strategy_label.pack()
strategy_combobox = ttk.Combobox(root, values=list(STRATEGIES.keys()))
strategy_combobox.pack()

load_data_button = ttk.Button(root, text="Load Data", command=load_data)
load_data_button.pack()

run_backtest_button = ttk.Button(root, text="Run Backtest", command=run_backtest)
run_backtest_button.pack()

root.mainloop()