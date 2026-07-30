import csv
import json
from pathlib import Path
from typing import List, Dict, Union
from models.entities import Student, Course, Grade
from models.enums import GradeCategory
from config.constants import GRADE_THRESHOLDS

class StorageService:
    @staticmethod
    def read_students_csv(file_path: Union[str, Path]) -> List[Student]:
        students = {}
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s_id = row['student_id']
                if s_id not in students:
                    students[s_id] = Student(
                        student_id=s_id,
                        name=row['name'],
                        major=row['major'],
                        year=int(row['year'])
                    )
                
                # 5. Create Grade object and add to course
                score = float(row['grade'])
                
                # Inline grading logic to keep GradeCategory simple
                if score >= GRADE_THRESHOLDS.get("A", 90):
                    cat = GradeCategory.EXCELLENT
                elif score >= GRADE_THRESHOLDS.get("B", 80):
                    cat = GradeCategory.GOOD
                elif score >= GRADE_THRESHOLDS.get("C", 70):
                    cat = GradeCategory.AVERAGE
                elif score >= GRADE_THRESHOLDS.get("D", 60):
                    cat = GradeCategory.PASS
                else:
                    cat = GradeCategory.FAIL

                grade_obj = Grade(score=score, category=cat)
                course = Course(course_name=row['course_name'], grade=grade_obj)
                students[s_id].courses.append(course)
        
        return list(students.values())

    @staticmethod
    def write_json_report(report_data: Dict, file_path: Union[str, Path]):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, mode='w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)
