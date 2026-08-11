# Student Grade Analytics Tool

A command-line tool that reads student grade records from a CSV file,
computes statistics and rankings using Python's built-in advanced
collection types (`Counter`, `defaultdict`, `OrderedDict`, `deque`), prints
a formatted terminal report, and writes a structured JSON analytics report.

This README is written to be self-sufficient: it documents not just *how*
to run the tool, but *why* it's built the way it is, so it can be read
end-to-end ahead of a code review.

## Table of contents

- [What it does](#what-it-does)
- [Setup](#setup)
- [Usage](#usage)
- [Sample output](#sample-output-stdout)
- [Sample JSON report](#sample-json-report-excerpt)
- [Project layout](#project-layout)
- [Module-by-module design notes](#module-by-module-design-notes)
- [The mode calculation, explicitly](#the-mode-calculation-explicitly)
- [Error handling](#error-handling)
- [Testing, formatting, and type-checking](#testing-formatting-and-type-checking)
- [Collection performance notes](#collection-performance-notes)
- [Anticipated review questions](#anticipated-review-questions)

## What it does

Given a CSV of per-course, per-semester scores (one row per student per
course per semester — see [Sample input](#usage)), the tool:

1. Loads the rows into typed `Student` and `GradeRecord` objects.
2. Aggregates them: grade distribution (A-F tally), scores grouped by
   student and by module, students ranked by average score against only
   their own (enrollment year, semester) peers — never against a
   different year, a different semester, or a different course.
3. Computes descriptive statistics: mean, median, mode, highest, lowest.
4. Assembles everything into one JSON-serializable report.
5. Prints a human-readable terminal report and writes the JSON report to
   disk.

The package is organized into four layers, each its own subpackage so
related files live together (see [Project layout](#project-layout)):
`models` (domain vocabulary), `analytics` (aggregation & statistics),
`file_io` (CSV/JSON persistence), and `reporting` (assembling and
presenting the report). `cli.py` is the composition root that wires them
together — the only module allowed to depend on all four. Dependency
direction only ever points inward (`cli` → `reporting`/`file_io` →
`analytics` → `models`), so there are no import cycles between layers.

## Setup

Requires Python 3.11+. Always use a project-local virtual environment —
never install dependencies globally.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt   # pytest, mypy, pytest-mock, black, ruff
pip install -e .                  # install this package in editable mode
```

## Usage

```bash
python main.py
# or, with explicit arguments:
python main.py --input data/sample_students.csv --output reports/grade_report.json --top-n 5
```

| Argument | Default | Meaning |
|---|---|---|
| `--input` | `data/sample_students.csv` | Path to the input CSV file |
| `--output` | `reports/grade_report.json` | Path to write the JSON report to |
| `--top-n` | `5` | Number of top performers to include in the report |

### Expected CSV format

```csv
student_id,name,module,year,course_code,semester,score
S001,Alice Uwase,CSC,2,CSC,Semester 1,88.5
S001,Alice Uwase,CSC,2,Math,Semester 1,91.0
```

One row is one student's score in one course during one semester.
`semester` only ever takes one of two values, `Semester 1` or
`Semester 2` — each academic `year` has exactly two of them, so the tool
never needs to reason about a growing, calendar-dated set of terms
(`Fall2023`, `Spring2024`, ...). `module` is the student's department/track,
abbreviated in the bundled sample data (`Math`, `CSC`, `PH`, `BIO`); it's a
single fixed value per student, separate from `course_code`, which is the
individual course a row's score belongs to. A student typically has
several rows per semester, one per course
(`course_code`); see [Module-by-module design notes](#module-by-module-design-notes)
for why ranking averages all of a student's courses in a semester rather
than comparing one course's score against another. In the bundled sample
data, every student in the same `(year, semester)` cohort takes the exact
same set of `course_code`s, regardless of their own `module` — a shared
curriculum per class year, not per department — so that comparing their
averages is comparing like with like. A student's identity fields (`name`,
`module`, `year`) are repeated on every one of their rows — a denormalized,
spreadsheet-friendly layout chosen because it's what a grade export from a
student information system typically looks like, and it keeps the loader a
single flat pass with no join step. When the same `student_id` appears on
multiple rows, the first occurrence wins for identity fields (see
[load_students.py](src/grade_analytics/file_io/load_students.py)); later
rows only contribute additional grade records.

Scores must be numeric and within `0.0`-`100.0`; anything else raises
`InvalidGradeRecordError` (see [Error handling](#error-handling)). The same
student also can't have two rows for the same `course_code` in the same
`semester` — that would double-count one course into their average — so
`load_grade_records_from_csv`/`stream_grade_records_from_csv` reject a
duplicate `(student_id, semester, course_code)` combination with the same
error.

### Sample output (stdout)

The terminal report ([render_report.py](src/grade_analytics/reporting/render_report.py))
uses plain ASCII tables (`+`/`-`/`|`) rather than Unicode box-drawing
characters, since those render reliably even in the legacy code page many
Windows consoles still default to. The distribution bar is the one exception —
it uses the Unicode block characters `█`/`░`, which render correctly on
UTF-8 terminals (Windows Terminal, VS Code's integrated terminal). Because
some Windows consoles default to a non-UTF-8 code page (e.g. `cp1252`) that
can't encode those block characters, `cli.py` reconfigures `stdout` to
UTF-8 on startup before printing anything (see
[cli.py](src/grade_analytics/cli.py)).

```
==============================================================================
                        STUDENT GRADE ANALYTICS REPORT
                 Generated: 2026-08-10T15:19:07.584846+00:00
==============================================================================

SUMMARY
  Total students      : 8
  Total grade records : 32
  Mean score          : 81.0
  Median score        : 84.75
  Mode                : 98.0
  Highest score       : 99.0
  Lowest score        : 55.0

GRADE DISTRIBUTION
+-------+-------+------------+--------------------------+
| Grade | Count | Percentage | Distribution             |
+-------+-------+------------+--------------------------+
| A     | 11    | 34.38%     | ████████░░░░░░░░░░░░░░░░ |
| B     | 8     | 25.00%     | ██████░░░░░░░░░░░░░░░░░░ |
| C     | 5     | 15.62%     | ████░░░░░░░░░░░░░░░░░░░░ |
| D     | 5     | 15.62%     | ████░░░░░░░░░░░░░░░░░░░░ |
| F     | 3     | 9.38%      | ██░░░░░░░░░░░░░░░░░░░░░░ |
+-------+-------+------------+--------------------------+

TOP PERFORMERS - Year 1, Semester 1
+------+----------------+------+------+------+
| Rank | Name           | BIO  | Math | Avg  |
+------+----------------+------+------+------+
| 1    | Grace Umutoni  | 92.0 | 90.0 | 91.0 |
| 2    | Carla Mukamana | 80.0 | 84.0 | 82.0 |
+------+----------------+------+------+------+

TOP PERFORMERS - Year 2, Semester 1
+------+-----------------+------+------+-------+
| Rank | Name            | CSC  | Math | Avg   |
+------+-----------------+------+------+-------+
| 1    | Alice Uwase     | 88.5 | 91.0 | 89.75 |
| 2    | David Niyonzima | 59.5 | 63.0 | 61.25 |
+------+-----------------+------+------+-------+

... (one TOP PERFORMERS table per (year, semester) group actually present
in the data — 8 groups for the bundled sample file, since each of the 4
years now has exactly two semesters, and every group has exactly the 2
students enrolled in that year. The two score columns are that group's
`courses` — the two `course_code`s shared by everyone in the group — not a
fixed pair across the whole report; Year 3's columns are `BIO`/`CSC`,
Year 4's are `Math`/`PH`. Trimmed here for brevity. A group larger than
`--top-n` also gets its own BOTTOM PERFORMERS table right after its TOP
PERFORMERS one — none of the sample groups are large enough to trigger
that at the default `--top-n 5`, but running with a smaller `--top-n`
(e.g. `--top-n 1`) shows it.)

MODULE BREAKDOWN
+--------+---------------+---------------+
| Module | Student Count | Average Score |
+--------+---------------+---------------+
| Math   | 2             | 74.62         |
| BIO    | 2             | 88.25         |
| CSC    | 2             | 82.88         |
| PH     | 2             | 78.25         |
+--------+---------------+---------------+

Report written to reports\grade_report.json
```

> Every student in the sample data takes multiple courses per semester
> (see the CSV's `course_code` column), and each ranking table has one
> column per course that group's students share, plus a final `Avg`
> column — the mean across *all* of a student's courses that semester,
> never a single course's score. So, for example, Alice Uwase's `Avg` of
> 89.75 in "Year 2, Semester 1" above is the average of her `CSC` (88.5)
> and `Math` (91.0) scores, not either one alone. Every student in a
> `(year, semester)` group takes the exact same `course_code`s as their
> peers in that group (a shared, standardized curriculum per class year),
> and each `student_id` appears in a semester's ranking exactly once, no
> matter how many courses they took that semester. Note that `MODULE
> BREAKDOWN` is unrelated to this per-course breakdown — it groups by each
> student's own fixed `module` (department), not by course.

### Sample JSON report (excerpt)

```json
{
  "generated_at": "2026-08-10T14:04:31.166371+00:00",
  "total_students": 8,
  "total_grade_records": 32,
  "overall_statistics": {
    "mean": 81.0,
    "median": 84.75,
    "mode": [98.0],
    "highest": 99.0,
    "lowest": 55.0
  },
  "grade_distribution": [
    { "letter_grade": "A", "count": 11, "percentage": 34.38 },
    { "letter_grade": "B", "count": 8, "percentage": 25.0 }
  ],
  "rankings_by_group": [
    {
      "year": 1,
      "semester": "Semester 1",
      "courses": ["BIO", "Math"],
      "top_performers": [
        { "rank": 1, "student_id": "S007", "name": "Grace Umutoni", "module": "BIO", "course_scores": { "Math": 90.0, "BIO": 92.0 }, "average_score": 91.0 },
        { "rank": 2, "student_id": "S003", "name": "Carla Mukamana", "module": "Math", "course_scores": { "Math": 84.0, "BIO": 80.0 }, "average_score": 82.0 }
      ],
      "bottom_performers": [],
      "full_ranking": [
        { "rank": 1, "student_id": "S007", "name": "Grace Umutoni", "module": "BIO", "course_scores": { "Math": 90.0, "BIO": 92.0 }, "average_score": 91.0 },
        { "rank": 2, "student_id": "S003", "name": "Carla Mukamana", "module": "Math", "course_scores": { "Math": 84.0, "BIO": 80.0 }, "average_score": 82.0 }
      ]
    }
  ],
  "module_breakdown": [
    { "module": "Math", "student_count": 2, "average_score": 74.62 }
  ]
}
```

`rankings_by_group` has one entry per (enrollment year, semester) pair
actually present in the data — students are ranked only against that
group's peers, never against a different year or semester (see
[Module-by-module design notes](#module-by-module-design-notes)). Each
group's `courses` lists the `course_code`s shared by that group, in the
same order the terminal table renders them as columns; each ranking
entry's `course_scores` gives that student's score in every one of them.

The full field set is defined by the `AnalyticsReport` `TypedDict` in
[build_report.py](src/grade_analytics/reporting/build_report.py). Within
each group, `top_performers` is that group's `full_ranking` truncated to
the first `--top-n` entries, and `bottom_performers` is the last `--top-n`
entries (empty once a group has `--top-n` students or fewer, since
everyone in it is already a top performer — see the example above);
`full_ranking` always contains every student in the group.

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

data/sample_students.csv        Sample input data
reports/                        Default output directory for the JSON report (git-ignored)
tests/                          pytest suite, mirroring src/grade_analytics/ 1:1
  models/  analytics/  file_io/  reporting/
  test_cli.py                     (cli.py has no dedicated subpackage to mirror)
```

## Module-by-module design notes

### `models/`

- **`entities.py`** — `Student` and `Course` are
  `@dataclass(frozen=True, slots=True)`: immutable (so they can't be
  accidentally mutated after being loaded) and slotted (no per-instance
  `__dict__`, which matters once thousands of records are held in memory
  at once — see [Collection performance notes](#collection-performance-notes)).
  `GradeRecord` and `RankedStudent` are `NamedTuple`s: simple, immutable,
  positional records with no behavior of their own, for which a
  `NamedTuple` is the lightest structure available.
- **`exceptions.py`** — a small hierarchy rooted at `StudentDataError`
  (see [Error handling](#error-handling)).
- **`grading_scale.py`** — a single pure function,
  `convert_score_to_letter_grade`, mapping a numeric score to a letter
  grade via an ordered threshold table.

### `analytics/`

- **`aggregate_records.py`** — grouping and tallying, each function named
  for exactly what it returns (`group_scores_by_student`,
  `group_students_by_module`, etc.), so the collection each one builds and
  its variable name always match:
  - `Counter` tallies how many records fall into each letter grade.
  - `OrderedDict` re-orders that tally into a fixed A-to-F display order,
    independent of insertion order or counts — needed because `Counter`
    and plain `dict` iteration order would otherwise follow whichever
    grades happened to appear first in the CSV.
  - `defaultdict(list)` groups students/scores by key (module, year,
    student id, semester) without a `key not in dict` check on every
    insert. `group_students_by_year_and_semester` and
    `group_records_by_year_and_semester` key on the combined
    `(year, semester)` pair, which is what lets `build_report.py` rank
    students against only their own year-and-semester peers instead of
    the entire student body. `group_scores_by_student_and_course` builds
    a `{student_id: {course_code: score}}` mapping — the source of each
    ranking entry's per-course column.
- **`calculate_statistics.py`** — mean/median delegate to the `statistics`
  module; mode, percentile rank, and highest/lowest are implemented
  directly (see [The mode calculation](#the-mode-calculation-explicitly)
  for why mode isn't a `statistics.mode()` call).
  `rank_students_by_average` implements **standard competition ranking**:
  students tied on average score share the same rank, and the next
  distinct rank skips ahead accordingly (1, 2, 2, 4 — not 1, 2, 2, 3). It
  operates on whatever `students`/`scores_by_student` it's given, which is
  what lets `build_report.py` call it once per `(year, semester)` group
  rather than once across everyone.
- **`track_rolling_average.py`** — `RollingAverageTracker` wraps a
  `deque(maxlen=window_size)`. This module is **not currently wired into
  the CLI or the report** — it's a standalone, independently tested
  utility for computing a semester-over-semester rolling average trend
  (`track_semester_trend`), demonstrating `deque`'s O(1) eviction of the
  oldest score via `maxlen` versus the O(n) slicing a plain `list` would
  need to stay bounded. If asked "where does this get used?", the honest
  answer is: it doesn't, yet — it's exercised only by its own test file.

### `file_io/`

- **`load_students.py`** — reads CSV rows via `csv.DictReader` behind a
  context manager. `load_students_from_csv` returns the *unique* students
  referenced in the file (first occurrence per `student_id` wins — see
  [Anticipated review questions](#anticipated-review-questions) for what
  happens when two rows disagree). `load_grade_records_from_csv` and
  `stream_grade_records_from_csv` return every row as a `GradeRecord`,
  routed through `_reject_duplicates`, which raises `InvalidGradeRecordError`
  if the same student's same `course_code` is recorded twice in the same
  `semester` — that would silently double-weight one course in the
  student's average otherwise. `stream_grade_records_from_csv` is a
  generator alternative for files too large to hold fully in memory.
  `parse_score` validates that every score is numeric and in `[0, 100]`.
- **`write_report.py`** — writes the `AnalyticsReport` dict to JSON with
  `json.dump`, creating parent directories as needed.

### `reporting/`

- **`build_report.py`** — pure assembly: takes students/records/statistics
  already computed by `analytics/` and shapes them into the
  `AnalyticsReport` `TypedDict` (and its nested `TypedDict`s
  `GradeDistributionEntry`, `RankingEntry`, `YearSemesterRanking`,
  `ModuleBreakdownEntry`, `SummaryStatistics`). Using `TypedDict` rather
  than a plain `dict` means `mypy --strict` catches a typo'd or missing
  report key at type-check time, while the value at runtime is still a
  plain JSON-serializable `dict` — no custom `to_dict()` step needed
  before `json.dump`. `build_rankings_by_group` produces
  `rankings_by_group`: one `YearSemesterRanking` per `(year, semester)`
  pair present in the data, each ranked independently on the mean of every
  course a student took that semester, so a first-year's single-semester
  average is never compared against a fourth-year's multi-semester one,
  and one course's score is never compared against a different course's.
  Each group also carries `courses` — the sorted, distinct `course_code`s
  shared by everyone in that group — and every `RankingEntry` carries a
  matching `course_scores` map, so the rendered table can show one column
  per course instead of a single aggregate figure. Each group's
  `bottom_performers` is the tail `--top-n` entries of its `full_ranking`
  (empty once the group has `--top-n` students or fewer).
- **`render_report.py`** — turns the report into the terminal text seen in
  [Sample output](#sample-output-stdout). `_build_ascii_table` is a small
  generic table renderer (headers + rows → bordered ASCII table) shared by
  every report table. `render_ranking_table` builds its header row as
  `Rank, Name, <one column per course>, Avg` — the course columns are
  read from the group's `courses` list, so they vary per `(year, semester)`
  group instead of being fixed. `render_group_rankings_section` renders
  one "TOP PERFORMERS" table per `(year, semester)` group in
  `rankings_by_group`, followed by a "BOTTOM PERFORMERS" table for that
  group whenever it has one.

### `cli.py`

The composition root: parses arguments, loads the CSV, calls
`build_analytics_report`, writes the JSON, prints the terminal report, and
translates any `StudentDataError` into a clean `SystemExit(1)` with a
message on stderr rather than a raw traceback.

## The mode calculation, explicitly

`calculate_mode` (in
[calculate_statistics.py](src/grade_analytics/analytics/calculate_statistics.py))
does **not** use `statistics.mode()`, because that function always returns
exactly one value and, on a tie, silently returns whichever tied value
happens to be encountered first — which isn't a meaningful answer for a
grade report. Instead:

- **Exactly one score repeats the most** → that score is *the* mode
  (a one-element list).
- **Two or more scores are tied for the highest frequency** → all of them
  are modes (a multi-element list) — the dataset is multimodal.
- **No score repeats at all** (every score is unique) → there is **no
  mode** (an empty list). `render_report.py` displays this case as the
  text "No mode" rather than picking an arbitrary value.

`overall_statistics.mode` in the JSON report is therefore always a list —
`[]`, `[x]`, or `[x, y, ...]` — never a bare number, so a consumer of the
JSON doesn't need to special-case "is this a list or a scalar?".

## Error handling

Every domain-specific error is a `StudentDataError` subclass (see
[exceptions.py](src/grade_analytics/models/exceptions.py)):

| Exception | Raised when |
|---|---|
| `StudentDataFileNotFoundError` | The input CSV path doesn't exist |
| `StudentDataFilePermissionError` | The input CSV can't be read, or the output path can't be written, due to file permissions |
| `InvalidGradeRecordError` | A CSV row is missing a required column, has a non-numeric score, or has a score outside `0-100` |

`cli.py` is the only place that catches `StudentDataError`: it prints
`Error: {message}` to stderr and exits with status `1`. Every lower layer
lets the exception propagate rather than catching-and-logging, so there's
exactly one place in the codebase that decides how a data error is
presented to the user.

Statistics functions that only make sense on a non-empty list
(`calculate_mean`, `calculate_median`, `calculate_mode`,
`calculate_percentile_rank`) raise a plain `ValueError` on an empty list —
these are programming-usage errors (calling a stats function with no
data), not user-facing data errors, so they deliberately don't go through
the `StudentDataError` hierarchy.

## Testing, formatting, and type-checking

```bash
pytest              # tests covering every module, mirroring src/grade_analytics/ 1:1
black src tests main.py
ruff check src tests main.py
mypy src tests main.py
```

`pyproject.toml` pins `mypy --strict` (`warn_unused_ignores`,
`explicit_package_bases`, and all standard strict flags), `black` at
100-character lines, and `ruff` with the `E, F, W, I, UP, B, N, C90`
rule sets — import sorting, pyupgrade, bugbear, naming, and complexity
checks alongside the usual pyflakes/pycodestyle.

### Coverage

Plain `pytest` — from anywhere, on any file or subset — just runs tests
and stays short:

```bash
pytest                                       # fast, no coverage table, run from anywhere
pytest --cov=grade_analytics --cov-report=term-missing --cov-fail-under=100
                                              # the full, gated check — run from the repo root before committing
```

Coverage is entirely opt-in, on purpose: `addopts` in `pyproject.toml`
carries no `--cov*` flags, so day-to-day test runs never print the
per-file table. The second command above is the one that matters for
enforcement — it fails unless every statement and branch in
`src/grade_analytics/` is covered by whatever ran, so it should be run
covering the *whole* suite (no path argument) from the repo root:

```bash
pytest --cov=grade_analytics --cov-report=term-missing --cov-fail-under=100
```

That prints a per-file coverage table with a `Missing` column naming any
uncovered line the moment a change under-tests something, rather than
letting a gap go unnoticed. The `[tool.coverage.report]` `exclude_lines`
setting excludes only the `if __name__ == "__main__":` script guard (which
runs only when the file is executed directly, never on import) — every
other line, including error branches (`PermissionError`, `ValueError` on
empty input, invalid CSV rows) and edge cases (an all-unique-scores
dataset with no mode, a module with no recorded scores) is exercised by an
explicit test rather than excluded.

Getting there took two small testability changes worth knowing about:

- `cli.py`'s UTF-8-stdout-reconfiguration logic was extracted into
  `_ensure_utf8_stdout(stream)`, a small function taking the stream as a
  parameter instead of reaching for `sys.stdout` directly — that's what
  let the tests exercise it with a real `io.TextIOWrapper` on a non-UTF-8
  encoding, without needing to mock `sys.stdout` itself (which pytest's
  own `capsys` fixture already replaces with something that isn't a
  `TextIOWrapper`, so the reconfigure branch would otherwise be
  unreachable in tests).
- `pytest-mock`'s `mocker.patch("builtins.open", side_effect=PermissionError)`
  simulates permission failures without needing an actual unreadable file
  on disk (which isn't reliable to set up cross-platform, especially on
  Windows).

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
- `GradeRecord` and `RankedStudent` use `NamedTuple` rather than a class,
  since they're simple, immutable, positional records with no behavior.
- `RollingAverageTracker` (see [track_rolling_average.py](src/grade_analytics/analytics/track_rolling_average.py))
  uses `deque(maxlen=window_size)` so tracking a trend across many semesters
  never grows unbounded and never needs manual truncation.
- `stream_grade_records_from_csv` is a generator alternative to
  `load_grade_records_from_csv` for processing CSV files too large to hold
  in memory as a list all at once.

## Anticipated review questions

**Why is `mode` a list instead of a single number?**
See [The mode calculation](#the-mode-calculation-explicitly) — a scalar
can't represent "no mode" or "multiple tied modes" without a magic value.

**Why `TypedDict` instead of a class (e.g. `dataclass` or Pydantic model)
for the report?**
The report's only job is to become JSON. A `TypedDict` gives static
type-checking of every key/value at zero runtime cost and serializes with
plain `json.dump` — no `.dict()`/`asdict()` conversion step, no extra
dependency.

**Why does `render_report.py` build ASCII tables by hand instead of using
a library like `rich` or `tabulate`?**
Zero extra runtime dependencies, and the table logic is small enough
(`_build_ascii_table`, ~15 lines) that a library would trade a few lines
of code for a new dependency to keep in sync with `mypy --strict`.

**Why does the CSV loader keep the *first* occurrence of a student's
name/module/year and ignore later ones instead of raising an error on a
mismatch?**
It's a deliberate simplicity trade-off: validating that every row for a
`student_id` agrees on identity fields would need a second pass (or
buffering) and a new exception type, for a condition that a well-formed
export shouldn't produce. The bundled sample data no longer contains a
row that exercises this (every student's identity is consistent across
their rows), but the rule is still implemented and worth knowing about if
a real export has a typo on a later row for the same student.

**Is there input validation on the CSV beyond the score range?**
`parse_score` validates score type and range (`0-100`). `year` is parsed
with `int()` and raises `InvalidGradeRecordError` on failure. The loader
also rejects a duplicate `(student_id, semester, course_code)` combination
(see the `load_students.py` note under
[Module-by-module design notes](#module-by-module-design-notes)) so the
same course can't be counted twice in one student's semester average.
Text fields (`name`, `module`,
`course_code`, `semester`) are otherwise taken as-is — there's no
whitelist of valid modules or course codes, since that's configuration the
tool doesn't own.

**Why was chart/PNG generation removed?**
An earlier version had a `visualize_report.py` module (matplotlib) behind
an opt-in `--visualize` flag. It was removed along with its test file and
the `matplotlib` dependency once it was no longer needed, so the tool now
has zero third-party runtime dependencies — only the dev/test tooling
(`pytest`, `mypy`, `black`, `ruff`) is a dependency at all.
