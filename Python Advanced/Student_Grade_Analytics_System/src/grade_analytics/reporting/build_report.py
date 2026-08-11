"""Assemble the full analytics report as a JSON-serializable ``TypedDict``."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from grade_analytics.analytics.aggregate_records import (
    count_grade_distribution,
    group_records_by_year_and_semester,
    group_scores_by_student,
    group_scores_by_student_and_course,
    group_students_by_module,
    group_students_by_year_and_semester,
    order_grade_distribution,
)
from grade_analytics.analytics.calculate_statistics import (
    calculate_mean,
    calculate_median,
    calculate_mode,
    find_highest_score,
    find_lowest_score,
    rank_students_by_average,
)
from grade_analytics.models.entities import GradeRecord, RankedStudent, Student


class GradeDistributionEntry(TypedDict):
    """One letter grade's share of all recorded grades."""

    letter_grade: str
    count: int
    percentage: float


class RankingEntry(TypedDict):
    """A single student's position on the leaderboard."""

    rank: int
    student_id: str
    name: str
    module: str
    course_scores: dict[str, float]
    average_score: float


class YearSemesterRanking(TypedDict):
    """Students ranked against only their own (enrollment year, semester) peers."""

    year: int
    semester: str
    courses: list[str]
    top_performers: list[RankingEntry]
    bottom_performers: list[RankingEntry]
    full_ranking: list[RankingEntry]


class ModuleBreakdownEntry(TypedDict):
    """Aggregate performance for one module."""

    module: str
    student_count: int
    average_score: float


class SummaryStatistics(TypedDict):
    """Overall descriptive statistics across every grade record."""

    mean: float
    median: float
    mode: list[float]
    highest: float
    lowest: float


class AnalyticsReport(TypedDict):
    """Top-level JSON report structure produced by this tool."""

    generated_at: str
    total_students: int
    total_grade_records: int
    overall_statistics: SummaryStatistics
    grade_distribution: list[GradeDistributionEntry]
    rankings_by_group: list[YearSemesterRanking]
    module_breakdown: list[ModuleBreakdownEntry]


def _convert_ranked_student_to_entry(
    ranked_student: RankedStudent, course_scores: dict[str, float]
) -> RankingEntry:
    return RankingEntry(
        rank=ranked_student.rank,
        student_id=ranked_student.student.student_id,
        name=ranked_student.student.name,
        module=ranked_student.student.module,
        course_scores=course_scores,
        average_score=round(ranked_student.average_score, 2),
    )


def build_grade_distribution_section(records: list[GradeRecord]) -> list[GradeDistributionEntry]:
    """Build the grade-distribution report section from ``records``."""
    total_record_count = len(records)
    if total_record_count == 0:
        return []
    ordered_distribution = order_grade_distribution(count_grade_distribution(records))
    return [
        GradeDistributionEntry(
            letter_grade=letter_grade,
            count=count,
            percentage=round((count / total_record_count) * 100.0, 2),
        )
        for letter_grade, count in ordered_distribution.items()
    ]


def build_module_breakdown_section(
    students: list[Student], scores_by_student: dict[str, list[float]]
) -> list[ModuleBreakdownEntry]:
    """Build the per-module aggregate performance report section."""
    students_by_module = group_students_by_module(students)
    breakdown_entries: list[ModuleBreakdownEntry] = []
    for module, module_students in students_by_module.items():
        module_scores = [
            score
            for student in module_students
            for score in scores_by_student.get(student.student_id, [])
        ]
        if not module_scores:
            continue
        breakdown_entries.append(
            ModuleBreakdownEntry(
                module=module,
                student_count=len(module_students),
                average_score=round(calculate_mean(module_scores), 2),
            )
        )
    return breakdown_entries


def build_rankings_by_group(
    students: list[Student], records: list[GradeRecord], top_n: int
) -> list[YearSemesterRanking]:
    """Rank students against only their own (enrollment year, semester) peers."""
    students_by_group = group_students_by_year_and_semester(students, records)
    records_by_group = group_records_by_year_and_semester(students, records)

    groups: list[YearSemesterRanking] = []
    for year, semester in sorted(students_by_group):
        group_records = records_by_group[(year, semester)]
        group_scores = group_scores_by_student(group_records)
        course_scores_by_student = group_scores_by_student_and_course(group_records)
        ranked_students = rank_students_by_average(
            students_by_group[(year, semester)], group_scores
        )
        ranking_entries = [
            _convert_ranked_student_to_entry(
                ranked_student, course_scores_by_student[ranked_student.student.student_id]
            )
            for ranked_student in ranked_students
        ]
        bottom_start = max(top_n, len(ranking_entries) - top_n)
        groups.append(
            YearSemesterRanking(
                year=year,
                semester=semester,
                courses=sorted({record.course_code for record in group_records}),
                top_performers=ranking_entries[:top_n],
                bottom_performers=ranking_entries[bottom_start:],
                full_ranking=ranking_entries,
            )
        )
    return groups


def build_analytics_report(
    students: list[Student], records: list[GradeRecord], top_n: int = 5
) -> AnalyticsReport:
    """Build the complete :class:`AnalyticsReport` from students and grade records."""
    scores_by_student = group_scores_by_student(records)
    all_scores = [record.score for record in records]

    return AnalyticsReport(
        generated_at=datetime.now(UTC).isoformat(),
        total_students=len(students),
        total_grade_records=len(records),
        overall_statistics=SummaryStatistics(
            mean=round(calculate_mean(all_scores), 2),
            median=round(calculate_median(all_scores), 2),
            mode=calculate_mode(all_scores),
            highest=find_highest_score(all_scores) or 0.0,
            lowest=find_lowest_score(all_scores) or 0.0,
        ),
        grade_distribution=build_grade_distribution_section(records),
        rankings_by_group=build_rankings_by_group(students, records, top_n),
        module_breakdown=build_module_breakdown_section(students, scores_by_student),
    )
