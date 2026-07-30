from typing import List
from models.entities import Student
from models.schemas import GradeAnalyticsReport
from services.distribution import DistributionService
from services.ranking import RankingService
from services.trend import TrendService

class ReportService:
    def __init__(self, students: List[Student]):
        self.students = students

    def generate_full_report(self) -> GradeAnalyticsReport:
        
        # Use the TypedDict constructor for clear type safety 
        return GradeAnalyticsReport(
            total_students=len(self.students),
            grade_distribution=DistributionService.calculate_grade_distribution(self.students),
            major_grouping=DistributionService.group_by_major(self.students),
            top_performers=RankingService(self.students).get_top_performers(),
            overall_average=RankingService.calculate_overall_average(self.students),
            rolling_averages=TrendService.calculate_rolling_averages(self.students)
        )

