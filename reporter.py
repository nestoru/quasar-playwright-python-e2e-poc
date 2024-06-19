import json
import os

class JSONReporter:
    def __init__(self):
        self.results = []

    def on_test_begin(self, test_name):
        self.test_name = test_name

    def on_test_end(self, status, error=None):
        data = {
            'title': self.test_name,
            'status': status,
            'error': error,
        }
        self.results.append(data)

    def on_end(self):
        output_dir = './test-results/json'
        os.makedirs(output_dir, exist_ok=True)
        report_file = os.path.join(output_dir, 'report.json')
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f'Consolidated report generated: {report_file}')

