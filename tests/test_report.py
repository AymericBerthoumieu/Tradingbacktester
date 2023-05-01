import pandas as pd
import matplotlib.pyplot as plt
from utils.report import ReportGenerator

path = "../reports/"

# Initialize the report generator with a file name
report_generator = ReportGenerator(path+"example_report.html")

# Add some text to the report
report_generator.add_text("This is a sample report.")

# Create a sample DataFrame
data = pd.DataFrame({
    "A": [1, 2, 3],
    "B": [4, 5, 6],
    "C": [7, 8, 9]
})

# Add the DataFrame to the report
report_generator.add_dataframe("Sample DataFrame", data)

# Create a sample chart
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [4, 5, 6])
ax.set_title("Sample Chart")

# Add the chart to the report
report_generator.add_chart("Sample Chart", fig)

# Generate the report and save it to a file
report_generator.generate_report()
