from typing import List, Optional
from models.entities import Student, Grade, TopPerformer

class RankingService:
    def __init__(self, students: List[Student]):
        self.students = students

    @staticmethod
    def _calculate_student_average(student: Student) -> float:
        if not student.courses:
            return 0.0
        return sum(c.grade.score for c in student.courses) / len(student.courses)

    def get_top_performers(self, n: int = 3) -> List[TopPerformer]:
        """Calculates average grade and finds top performers."""
        student_averages = []
        for student in self.students:
            avg = self._calculate_student_average(student)
            student_averages.append(TopPerformer(name=student.name, average_score=round(avg, 2)))
        
        return sorted(student_averages, key=lambda x: x.average_score, reverse=True)[:n]

    def get_highest_grade_in_course(self, course_name: str) -> Optional[Grade]:
        best_grade = None
        for student in self.students:
            for course in student.courses:
                if course.course_name == course_name:
                    if best_grade is None or course.grade.score > best_grade.score:
                        best_grade = course.grade
        return best_grade

    @staticmethod
    def calculate_overall_average(students: List[Student]) -> float:
        all_grades = [c.grade.score for s in students for c in s.courses]
        return round(sum(all_grades) / len(all_grades), 2) if all_grades else 0.0
