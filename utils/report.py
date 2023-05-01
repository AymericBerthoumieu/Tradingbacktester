import base64
from io import BytesIO


class ReportGenerator:
    """
    A class for generating reports with text, charts, and pandas dataframes in HTML format.
    """

    def __init__(self, file_name):
        """
        Initialize the report generator with a file name.
        """
        self.file_name = file_name
        self.report_data = []

    def add_text(self, text):
        """
        Add a text block to the report.
        """
        self.report_data.append(f"<p>{text}</p>")

    def add_dataframe(self, title, data):
        """
        Add a pandas DataFrame to the report with a title.
        """
        # Add the title
        self.report_data.append(f"<h2>{title.upper()}</h2>")

        # Convert the DataFrame to an HTML table and add it to the report
        self.report_data.append(data.to_html(index=False))

    def add_chart(self, title, chart):
        """
        Add a matplotlib chart to the report with a title.
        """
        tmpfile = BytesIO()
        chart.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        html = '<img src=\'data:image/png;base64,{}\'>'.format(encoded)
        self.report_data.append(html)

    def generate_report(self):
        """
        Generate the report in HTML format and save it to a file.
        """
        report = "\n".join(self.report_data)

        with open(self.file_name, 'w') as f:
            f.write(report)
