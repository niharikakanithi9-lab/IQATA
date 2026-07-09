from datetime import datetime
from database.sqlite_db import SQLiteDB
from analytics.metrics import Metrics

import joblib
import pandas as pd


class QAReport:

    def __init__(self):
        self.metrics = Metrics()


    def get_ai_prediction(self):

        model = joblib.load("ml/model.pkl")


        data = pd.DataFrame([
            {
                "module": "Checkout",
                "browser": "Chrome",
                "environment": "Production",
                "priority": 0.95,
                "execution_time": 5.2
            }
        ])


        probability = model.predict_proba(data)

        risk = round(probability[0][1] * 100, 2)


        if risk > 50:
            result = "HIGH RISK"
        else:
            result = "LOW RISK"


        return result, risk


    
    def generate_report(self):

        report = []

        report.append("=" * 50)
        report.append("INTELLIGENT QA AUTOMATION REPORT")
        report.append("=" * 50)

        report.append(f"Generated On : {datetime.now()}")

        report.append("")
        report.append("TEST SUMMARY")
        report.append("-" * 50)

        report.append(f"Total Test Cases       : {self.metrics.total_test_cases()}")
        report.append(f"Total Test Runs        : {self.metrics.total_test_runs()}")
        report.append("")

        report.append("Execution Source")
        report.append("-" * 50)
        report.append("Historical Test Runs : Generated Dataset")
        report.append("Latest Test Runs     : Live Selenium Automation")
        report.append("")
        report.append("LATEST AUTOMATION TESTS")
        risk, probability = self.get_ai_prediction()

        report.append("")
        report.append("AI DEFECT PREDICTION")
        report.append("-"*50)

        report.append(
        f"Checkout Test : {risk} ({probability}% failure probability)"
        )   
        report.append("-" * 50)
        db = SQLiteDB()
        db.connect()
        latest = db.fetchall("""
SELECT tc.name,
       tr.status,
       tr.execution_time
FROM test_runs tr
JOIN test_cases tc
ON tr.test_case_id = tc.id
WHERE tc.name IN
(
'Login Test',
'Search Test',
'Checkout Test'
)
ORDER BY tr.id DESC
LIMIT 3
        """)

        for name, status, exec_time in reversed(latest):
            report.append(f"{name:<18} {status:<6} {exec_time:.2f} sec")
        db.close()
        report.append(f"Passed Tests           : {self.metrics.passed_tests()}")
        report.append(f"Failed Tests           : {self.metrics.failed_tests()}")
        report.append(f"Pass Rate              : {self.metrics.pass_rate()} %")
        report.append(f"Failure Rate           : {self.metrics.failure_rate()} %")
        report.append(f"Average Execution Time : {self.metrics.average_execution_time()} sec")

        report.append("")
        report.append("BROWSER DISTRIBUTION")
        report.append("-" * 50)

        for browser, count in self.metrics.browser_statistics():
            report.append(f"{browser:<15} : {count}")

        report.append("")
        report.append("ENVIRONMENT DISTRIBUTION")
        report.append("-" * 50)

        for env, count in self.metrics.environment_statistics():
            report.append(f"{env:<15} : {count}")

        report.append("")
        report.append("MODULE DISTRIBUTION")
        report.append("-" * 50)

        for module, count in self.metrics.module_statistics():
            report.append(f"{module:<20} : {count}")

        return "\n".join(report)
    
    def save_report(self, filename="reports/qa_report.txt"):

        report = self.generate_report()

        with open(filename, "w") as file:
            file.write(report)

        print(f"Report saved successfully: {filename}")

        self.metrics.close()


if __name__ == "__main__":

    report = QAReport()

    print(report.generate_report())

    report.save_report()