from collections import Counter, defaultdict
from typing import List, Dict
from models.entities import Student

class DistributionService:
    @staticmethod
    def calculate_grade_distribution(students: List[Student]) -> Dict[str, int]:
        """Uses Counter to count grade categories."""
        grades = []
        for student in students:
            for course in student.courses:
                grades.append(course.grade.category.value)
        return dict(Counter(grades))

    @staticmethod
    def calculate_mode(students: List[Student]) -> str:
        """Calculates the mode (most common grade) using Counter."""
        grades = []
        for student in students:
            for course in student.courses:
                grades.append(course.grade.category.value)
        
        if not grades:
            return "N/A"

        return Counter(grades).most_common(1)[0][0]

    @staticmethod
    def group_by_major(students: List[Student]) -> Dict[str, List[str]]:
        """Groups student names by major."""
        major_map = defaultdict(list)
        for student in students:
            major_map[student.major].append(student.name)
        return dict(major_map)
