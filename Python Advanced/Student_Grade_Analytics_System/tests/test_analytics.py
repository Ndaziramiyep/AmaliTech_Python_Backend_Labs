from src.models.entities import Student, Course, Grade
from src.models.enums import GradeCategory
from src.services.distribution import DistributionService
from src.services.ranking import RankingService
from src.services.trend import TrendService
import pytest

@pytest.fixture
def sample_students():
    return [
        Student(
            student_id="1", name="Alice", major="CS", year=2,
            courses=[
                Course("Python", Grade(95, GradeCategory.EXCELLENT)),
                Course("Algorithms", Grade(85, GradeCategory.GOOD))
            ]
        ),
        Student(
            student_id="2", name="Bob", major="Math", year=1,
            courses=[
                Course("Calc", Grade(75, GradeCategory.AVERAGE))
            ]
        )
    ]

def test_grade_distribution(sample_students):
    dist = DistributionService.calculate_grade_distribution(sample_students)
    assert dist['A'] == 1
    assert dist['B'] == 1
    assert dist['C'] == 1

def test_group_by_major(sample_students):
    majors = DistributionService.group_by_major(sample_students)
    assert 'CS' in majors
    assert 'Alice' in majors['CS']
    assert 'Bob' in majors['Math']

def test_top_performers(sample_students):
    ranking_service = RankingService(sample_students)
    top = ranking_service.get_top_performers()
    # top[0] is a TopPerformer NamedTuple
    assert top[0].name == 'Alice'
    assert top[0].average_score == 90.0

def test_rolling_average(sample_students):
    rolling = TrendService.calculate_rolling_averages(sample_students, window_size=2)
    # Alice: [95, 85] -> [95, 90]
    assert rolling['Alice'] == [95.0, 90.0]
