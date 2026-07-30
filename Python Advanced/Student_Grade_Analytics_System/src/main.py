from services.storage import StorageService
from services.report import ReportService
from ui.cli import CLI
from pathlib import Path

def main():
    data_path = Path("data/students.csv")
    report_path = Path("data/report.json")

    CLI.display_welcome()
    
    try:
        # 1. Load Data
        CLI.display_loading(data_path)
        students = StorageService.read_students_csv(data_path)
        
        # 2. Analyze
        CLI.display_analyzing()
        service = ReportService(students)
        report = service.generate_full_report()
        
        # 3. Output results to console
        CLI.display_summary(report)

        # 4. Save Report
        StorageService.write_json_report(report, report_path)
        CLI.display_success(report_path)

    except FileNotFoundError as e:
        CLI.display_error(e)
    except Exception as e:
        CLI.display_unexpected_error(e)

if __name__ == "__main__":
    main()
