"""Collection-based aggregation of students and grade records."""

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
        (letter_grade, distribution[letter_grade])
        for letter_grade in _GRADE_DISPLAY_ORDER
        if letter_grade in distribution
    )


def group_students_by_major(students: list[Student]) -> defaultdict[str, list[Student]]:
    """Group ``students`` into lists keyed by their major."""
    students_by_major: defaultdict[str, list[Student]] = defaultdict(list)
    for student in students:
        students_by_major[student.major].append(student)
    return students_by_major


def group_students_by_year(students: list[Student]) -> defaultdict[int, list[Student]]:
    """Group ``students`` into lists keyed by their enrollment year."""
    students_by_year: defaultdict[int, list[Student]] = defaultdict(list)
    for student in students:
        students_by_year[student.year].append(student)
    return students_by_year


def group_students_by_year_and_semester(
    students: list[Student], records: list[GradeRecord]
) -> defaultdict[tuple[int, str], list[Student]]:
    """Group ``students`` into lists keyed by (enrollment year, semester) pairs from ``records``."""
    students_by_id = {student.student_id: student for student in students}
    seen_keys: set[tuple[int, str, str]] = set()
    grouped: defaultdict[tuple[int, str], list[Student]] = defaultdict(list)
    for record in records:
        student = students_by_id[record.student_id]
        dedup_key = (student.year, record.semester, student.student_id)
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            grouped[(student.year, record.semester)].append(student)
    return grouped


def group_scores_by_student(records: list[GradeRecord]) -> defaultdict[str, list[float]]:
    """Group every score in ``records`` into a list keyed by student id."""
    scores_by_student: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        scores_by_student[record.student_id].append(record.score)
    return scores_by_student


def group_scores_by_semester(records: list[GradeRecord]) -> defaultdict[str, list[float]]:
    """Group every score in ``records`` into a list keyed by semester."""
    scores_by_semester: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        scores_by_semester[record.semester].append(record.score)
    return scores_by_semester
