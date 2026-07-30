# Student Grade Analytics Tool

A command-line tool that reads student grade records from CSV, computes
statistics and rankings using Python's advanced collection types, and
writes a structured JSON analytics report.

## Features

The package is organized into four layers, each its own subpackage so
related files live together (see [Project layout](#project-layout)):
`models` (domain vocabulary), `analytics` (aggregation & statistics),
`file_io` (CSV/JSON persistence), and `reporting` (assembling and
presenting the report). `cli.py` is the composition root that wires them
together — the only module allowed to depend on all four.

- **Data models**: immutable, slotted `dataclass` models (`Student`, `Course`)
  and a `NamedTuple` model (`GradeRecord`) — see [src/grade_analytics/models/entities.py](src/grade_analytics/models/entities.py)
- **Collections**: `Counter` for grade tallies, `defaultdict` for grouping,
  `OrderedDict` for deterministic report ordering, `deque` for a rolling
  average — see [src/grade_analytics/analytics/aggregate_records.py](src/grade_analytics/analytics/aggregate_records.py)
  and [src/grade_analytics/analytics/track_rolling_average.py](src/grade_analytics/analytics/track_rolling_average.py)
- **File I/O**: `csv.DictReader` and `json.dump`, both behind context
  managers and `pathlib.Path`, with domain-specific errors for missing
  files, permission errors, and malformed rows — see
  [src/grade_analytics/file_io/load_students.py](src/grade_analytics/file_io/load_students.py)
- **Statistics**: mean, median, mode, percentile rank, and competition-style
  ranking — see [src/grade_analytics/analytics/calculate_statistics.py](src/grade_analytics/analytics/calculate_statistics.py)
- **Reporting**: a `TypedDict`-typed JSON report assembled from the above —
  see [src/grade_analytics/reporting/build_report.py](src/grade_analytics/reporting/build_report.py)
- **Terminal report**: a formatted, ASCII-table report (summary, grade
  distribution with an inline bar chart, top performers, major breakdown)
  printed on every run — see [src/grade_analytics/reporting/render_report.py](src/grade_analytics/reporting/render_report.py)
- **Visualizations** (opt-in via `--visualize`): PNG bar charts for grade
  distribution, top performers, and average score by major — see
  [src/grade_analytics/reporting/visualize_report.py](src/grade_analytics/reporting/visualize_report.py)

## Setup

Requires Python 3.11+. Always use a project-local virtual environment —
never install dependencies globally.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt   # pytest, mypy, pytest-mock, black, ruff, matplotlib
pip install -e .                      # install this package in editable mode
```

## Usage

```bash
python main.py
# or, with explicit arguments:
python main.py --input data/sample_students.csv --output reports/grade_report.json --top-n 5

# also render PNG charts (grade distribution, top performers, major breakdown):
python main.py --visualize --charts-dir reports/charts
```

### Sample output (stdout)

The terminal report ([render_report.py](src/grade_analytics/reporting/render_report.py))
uses plain ASCII tables (`+`/`-`/`|`) rather than Unicode box-drawing
characters, since those render reliably even in the legacy code page many
Windows consoles still default to:

```
==============================================================================
                        STUDENT GRADE ANALYTICS REPORT
                 Generated: 2026-07-29T14:19:12.787576+00:00
==============================================================================

SUMMARY
  Total students      : 8
  Total grade records : 32
  Mean score          : 81.27
  Median score        : 83.0
  Mode                : 88.5, 91.0, 93.5, 95.0, 97.0, ...
  Highest score       : 99.0
  Lowest score        : 55.0

GRADE DISTRIBUTION
+-------+-------+------------+--------------------------+
| Grade | Count | Percentage | Distribution             |
+-------+-------+------------+--------------------------+
| A     | 11    | 34.38%     | ########................ |
| B     | 8     | 25.00%     | ######.................. |
| C     | 6     | 18.75%     | ####.................... |
| D     | 4     | 12.50%     | ###..................... |
| F     | 3     | 9.38%      | ##...................... |
+-------+-------+------------+--------------------------+

TOP PERFORMERS
+------+---------------+------------------+---------------+
| Rank | Name          | Major            | Average Score |
+------+---------------+------------------+---------------+
| 1    | Elena Petrova | Physics          | 97.0          |
| 2    | Alice Johnson | Computer Science | 93.0          |
| 3    | Grace Owusu   | Biology          | 91.25         |
| 4    | Carla Mendes  | Mathematics      | 86.0          |
| 5    | Henry Adeyemi | Biology          | 82.4          |
+------+---------------+------------------+---------------+

MAJOR BREAKDOWN
+------------------+---------------+---------------+
| Major            | Student Count | Average Score |
+------------------+---------------+---------------+
| Computer Science | 2             | 84.1          |
| Mathematics      | 2             | 72.21         |
| Physics          | 2             | 82.44         |
| Biology          | 2             | 84.93         |
+------------------+---------------+---------------+

Report written to reports\grade_report.json
```

> Add a screenshot of this output (e.g. `docs/execution.png`) after running
> the command locally.

### Sample charts

| Grade distribution | Top performers | Average score by major |
|---|---|---|
| ![Grade distribution](docs/sample_charts/grade_distribution.png) | ![Top performers](docs/sample_charts/top_performers.png) | ![Average score by major](docs/sample_charts/major_breakdown.png) |

### Sample JSON report (excerpt)

```json
{
  "generated_at": "2026-07-29T10:38:42.467476+00:00",
  "total_students": 8,
  "total_grade_records": 32,
  "overall_statistics": {
    "mean": 81.27,
    "median": 83.0,
    "mode": [88.5, 91.0, "..."],
    "highest": 99.0,
    "lowest": 55.0
  },
  "grade_distribution": [
    { "letter_grade": "A", "count": 11, "percentage": 34.38 },
    { "letter_grade": "B", "count": 8, "percentage": 25.0 }
  ],
  "top_performers": [
    { "rank": 1, "student_id": "S005", "name": "Elena Petrova", "major": "Physics", "average_score": 97.0 }
  ],
  "major_breakdown": [
    { "major": "Computer Science", "student_count": 2, "average_score": 84.1 }
  ]
}
```

The full field set is defined by the `AnalyticsReport` `TypedDict` in
[build_report.py](src/grade_analytics/reporting/build_report.py).

## Project layout

Each subpackage groups files by the single responsibility it owns, so
related code — and its mirrored test folder — always live together:

```
src/grade_analytics/
  cli.py                          Argument parsing and orchestration (composition root)
  models/                         Domain vocabulary — no dependencies on other layers
    entities.py                     Student, Course, GradeRecord, RankedStudent
    exceptions.py                   Domain-specific error types
    grading_scale.py                Score -> letter grade conversion
  analytics/                      Aggregation & statistics — depends only on models/
    aggregate_records.py            Counter / defaultdict / OrderedDict aggregation
    calculate_statistics.py         mean / median / mode / percentile / ranking
    track_rolling_average.py        deque-backed rolling average tracker
  file_io/                        Reading/writing files — depends only on models/ + reporting/
    load_students.py                CSV loading (list + generator variants)
    write_report.py                 JSON report writer
  reporting/                      Assembling & presenting the report — depends on models/ + analytics/
    build_report.py                 TypedDict report assembly
    render_report.py                ASCII terminal report rendering
    visualize_report.py             PNG chart generation (matplotlib, Agg backend)

data/sample_students.csv        Sample input data
tests/                          pytest suite, mirroring src/grade_analytics/ 1:1
  models/  analytics/  file_io/  reporting/
  test_cli.py                     (cli.py has no dedicated subpackage to mirror)
```

Dependency direction only ever points inward/downward (`cli` → `reporting`/
`file_io` → `analytics` → `models`), so there are no import cycles between
layers.

## Testing, formatting, and type-checking

```bash
pytest              # 74 tests covering every module
black src tests main.py
ruff check src tests main.py
mypy src tests main.py
```

## Collection performance notes

Measured with `sys.getsizeof` on this machine (CPython 3.14); exact byte
counts vary by interpreter version but the relative differences hold.

| Structure | Size | Notes |
|---|---|---|
| Slotted, frozen `dataclass` (`Student`) | 64 bytes | No per-instance `__dict__`; used for all data models |
| Plain `dataclass`, no `slots` | 48 + 296 (dict) = 344 bytes | ~5x larger than the slotted version once its `__dict__` is counted |
| `NamedTuple` equivalent | 80 bytes | Comparable to slots; also gives free tuple unpacking |
| `list` of 100,000 floats | ~800 KB | Loaded fully into memory |
| Generator yielding the same 100,000 floats | 216 bytes (constant) | Used by `stream_grade_records_from_csv` for large files — O(1) memory instead of O(n) |
| `deque(maxlen=N)` vs `list` for a rolling window | deque overhead is higher per-object for small N | The point of `deque` here isn't raw size — it's O(1) amortized eviction of the oldest score via `maxlen`, versus O(n) slicing to truncate a `list` on every update |

**Takeaways applied in this codebase:**
- `Student` and `Course` use `@dataclass(frozen=True, slots=True)` to avoid
  the per-instance `__dict__` overhead, since many student records are held
  in memory at once.
- `GradeRecord` uses `NamedTuple` rather than a class, since it's a simple,
  immutable, positional record with no behavior.
- `RollingAverageTracker` (see [track_rolling_average.py](src/grade_analytics/analytics/track_rolling_average.py))
  uses `deque(maxlen=window_size)` so tracking a trend across many semesters
  never grows unbounded and never needs manual truncation.
- `stream_grade_records_from_csv` is a generator alternative to
  `load_grade_records_from_csv` for processing CSV files too large to hold
  in memory as a list all at once.
