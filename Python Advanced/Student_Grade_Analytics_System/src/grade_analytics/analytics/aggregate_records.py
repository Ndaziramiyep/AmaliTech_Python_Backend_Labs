"""Collection-based aggregation of students and grade records.

Uses :class:`collections.Counter` for tallying, :class:`collections.defaultdict`
for grouping, and :class:`collections.OrderedDict` for report sections whose
key order must be deterministic and independent of insertion or count order.
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict

from grade_analytics.models.entities import GradeRecord, Student
from grade_analytics.models.grading_scale import convert_score_to_letter_grade

_GRADE_DISPLAY_ORDER: tuple[str, ...] = ("A", "B", "C", "D", "F")


def count_grade_distribution(records: list[GradeRecord]) -> Counter[str]:
    """Tally how many ``records`` fall into each letter grade."""
    return Counter(convert_score_to_letter_grade(record.score) for record in records)


def order_grade_distribution(distribution: Counter[str]) -> OrderedDict[str, int]:
    """Return ``distribution`` as an ``OrderedDict`` in A-to-F display order."""
    return OrderedDict(
        (letter, distribution[letter]) for letter in _GRADE_DISPLAY_ORDER if letter in distribution
    )


def group_students_by_major(students: list[Student]) -> defaultdict[str, list[Student]]:
    """Group ``students`` into lists keyed by their major."""
    grouped: defaultdict[str, list[Student]] = defaultdict(list)
    for student in students:
        grouped[student.major].append(student)
    return grouped


def group_students_by_year(students: list[Student]) -> defaultdict[int, list[Student]]:
    """Group ``students`` into lists keyed by their enrollment year."""
    grouped: defaultdict[int, list[Student]] = defaultdict(list)
    for student in students:
        grouped[student.year].append(student)
    return grouped


def group_scores_by_student(records: list[GradeRecord]) -> defaultdict[str, list[float]]:
    """Group every score in ``records`` into a list keyed by student id."""
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[record.student_id].append(record.score)
    return grouped


def group_scores_by_semester(records: list[GradeRecord]) -> defaultdict[str, list[float]]:
    """Group every score in ``records`` into a list keyed by semester."""
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[record.semester].append(record.score)
    return grouped
