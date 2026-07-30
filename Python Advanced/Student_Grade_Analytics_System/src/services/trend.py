from collections import deque
from typing import List, Dict
from models.entities import Student
from config.constants import DEFAULT_WINDOW_SIZE

class TrendService:
    @staticmethod
    def calculate_rolling_averages(students: List[Student], window_size: int = DEFAULT_WINDOW_SIZE) -> Dict[str, List[float]]:
        """Uses deque to implement a rolling average for each student's grades."""
        rolling_avgs = {}
        for student in students:
            grades = [c.grade for c in student.courses]
            if not grades:
                continue
            
            dq: deque[float] = deque(maxlen=window_size)
            student_rolling = []
            for grade in grades:
                dq.append(grade.score)
                student_rolling.append(round(sum(dq) / len(dq), 2))
            rolling_avgs[student.name] = student_rolling
        return rolling_avgs
