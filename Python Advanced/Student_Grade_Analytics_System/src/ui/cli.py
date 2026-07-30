class CLI:
    @staticmethod
    def display_welcome():
        print("--- Student Grade Analytics Tool ---")

    @staticmethod
    def display_loading(path):
        print(f"Loading data from {path}...")

    @staticmethod
    def display_analyzing():
        print("Analyzing performance...")

    @staticmethod
    def display_summary(report):
        print(f"\nTotal Students: {report['total_students']}")
        print(f"Overall Average: {report['overall_average']:.2f}") # Standardize to 2 decimal places
        
        print("\nGrade Distribution:")
        for grade, count in report['grade_distribution'].items():
            print(f"  {grade}: {count}")
            
        print("\nTop 3 Performers:")
        # Ensure 'top_performers' are always dictionaries for consistent access
        for i, p in enumerate(report['top_performers'][:3], 1):
            name = p.name
            score = p.average_score
            print(f"  {i}. {name} ({score:.2f})")

        if 'major_grouping' in report and report['major_grouping']:
            print("\nStudents by Major:")
            for major, students in report['major_grouping'].items():
                print(f"  {major}: {len(students)} students")

        if 'rolling_averages' in report and report['rolling_averages']:
            print("\nRolling Averages (last 3 students):")
            # Get last 3 items from dict
            last_3_items = list(report['rolling_averages'].items())[-3:]
            for i, (student_name, avgs) in enumerate(last_3_items, 1):
                latest_avg = avgs[-1] if avgs else 0.0
                print(f"  {student_name}: {latest_avg:.2f}") 

    @staticmethod
    def display_success(path):
        print(f"\nReport successfully saved to {path}")

    @staticmethod
    def display_error(error):
        print(f"Error: {error}")

    @staticmethod
    def display_unexpected_error(error):
        print(f"An unexpected error occurred: {error}")
