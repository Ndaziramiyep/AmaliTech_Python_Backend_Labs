# Lab 1: Student Grade Analytics Tool

This tool processes student records from a CSV file and generates a comprehensive analytics report in JSON format.

## Features
- **Data Modeling**: Uses `dataclasses` and `TypedDict` for structured student and course information.
- **Advanced Collections**:
    - `Counter`: For grade distribution analysis.
    - `defaultdict`: For grouping students by major.
    - `OrderedDict`: To maintain the order of report sections.
    - `deque`: For calculating rolling averages of grades.
- **File I/O**: Robust CSV reading and JSON writing using context managers and `pathlib`.
- **Type Hinting**: Comprehensive use of Python type hints for static analysis.

## Setup
1. Ensure you have Python 3.11+ installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the main script from the root directory:
```bash
python src/main.py
```

## Sample Output
```text
--- Student Grade Analytics Tool ---
Loading data from data/students.csv...
Analyzing performance...

Total Students: 5
Overall Average: 87.64

Grade Distribution:
  A: 6
  B: 3
  C: 2

Top 3 Performers:
  1. Eva Davis (95.0)
  2. Alice Johnson (91.67)
  3. Charlie Brown (88.0)

Report successfully saved to data/report.json
```
