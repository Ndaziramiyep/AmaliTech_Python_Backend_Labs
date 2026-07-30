"""Assemble the full analytics report as a JSON-serializable ``TypedDict``."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from grade_analytics.analytics.aggregate_records import (
    count_grade_distribution,
    group_scores_by_student,
    group_students_by_major,
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
    major: str
    average_score: float


class MajorBreakdownEntry(TypedDict):
    """Aggregate performance for one major."""

    major: str
    student_count: int
    average_score: float


class SummaryStatistics(TypedDict):
    """Overall descriptive statistics across every grade record."""

    mean: float
    median: float
    mode: float
    highest: float
    lowest: float


class AnalyticsReport(TypedDict):
    """Top-level JSON report structure produced by this tool."""

    generated_at: str
    total_students: int
    total_grade_records: int
    overall_statistics: SummaryStatistics
    grade_distribution: list[GradeDistributionEntry]
    top_performers: list[RankingEntry]
    full_ranking: list[RankingEntry]
    major_breakdown: list[MajorBreakdownEntry]


def _convert_ranked_student_to_entry(ranked_student: RankedStudent) -> RankingEntry:
    return RankingEntry(
        rank=ranked_student.rank,
        student_id=ranked_student.student.student_id,
        name=ranked_student.student.name,
        major=ranked_student.student.major,
        average_score=round(ranked_student.average_score, 2),
    )


def build_grade_distribution_section(records: list[GradeRecord]) -> list[GradeDistributionEntry]:
    """Build the grade-distribution report section from ``records``."""
    total = len(records)
    if total == 0:
        return []
    ordered_distribution = order_grade_distribution(count_grade_distribution(records))
    return [
        GradeDistributionEntry(
            letter_grade=letter,
            count=count,
            percentage=round((count / total) * 100.0, 2),
        )
        for letter, count in ordered_distribution.items()
    ]


def build_major_breakdown_section(
    students: list[Student], scores_by_student: dict[str, list[float]]
) -> list[MajorBreakdownEntry]:
    """Build the per-major aggregate performance report section."""
    grouped_by_major = group_students_by_major(students)
    breakdown: list[MajorBreakdownEntry] = []
    for major, major_students in grouped_by_major.items():
        major_scores = [
            score
            for student in major_students
            for score in scores_by_student.get(student.student_id, [])
        ]
        if not major_scores:
            continue
        breakdown.append(
            MajorBreakdownEntry(
                major=major,
                student_count=len(major_students),
                average_score=round(calculate_mean(major_scores), 2),
            )
        )
    return breakdown


def build_analytics_report(
    students: list[Student], records: list[GradeRecord], top_n: int = 5
) -> AnalyticsReport:
    """Build the complete :class:`AnalyticsReport` from students and grade records."""
    scores_by_student = group_scores_by_student(records)
    all_scores = [record.score for record in records]
    ranked_students = rank_students_by_average(students, scores_by_student)
    ranking_entries = [_convert_ranked_student_to_entry(entry) for entry in ranked_students]

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
        top_performers=ranking_entries[:top_n],
        full_ranking=ranking_entries,
        major_breakdown=build_major_breakdown_section(students, scores_by_student),
    )
