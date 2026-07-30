from models.entities import TopPerformer
from typing import Dict, List, TypedDict



class GradeAnalyticsReport(TypedDict):
    total_students: int
    grade_distribution: Dict[str, int]
    major_grouping: Dict[str, List[str]]
    top_performers: List[TopPerformer]
    overall_average: float
    rolling_averages: Dict[str, List[float]]
