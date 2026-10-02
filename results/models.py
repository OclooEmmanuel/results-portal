from django.db import models
from students.models import Student


class Result(models.Model):
    SUBJECT_FIELDS = (
        ("maths", "Mathematics"),
        ("english", "English Language"),
        ("science", "Integrated Science"),
        ("social_studies", "Social Studies"),
        ("rme", "R.M.E"),
        ("computing", "Computing"),
        ("carear_tech", "Career Technology"),
        ("cad", "Creative Arts & Design"),
        ("asante_twi", "Asante Twi"),
        ("french", "French"),
    )

    CORE_SUBJECTS = ("english", "maths", "science", "social_studies")

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="results",
    )
    mock_number = models.CharField(max_length=2, blank=True)

    maths = models.IntegerField()
    english = models.IntegerField()
    science = models.IntegerField()
    social_studies = models.IntegerField()
    rme = models.IntegerField()
    computing = models.IntegerField()
    carear_tech = models.IntegerField()
    cad = models.IntegerField()
    asante_twi = models.IntegerField()
    french = models.IntegerField()
    remark = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ("student", "mock_number")

    def __str__(self):
        return f"{self.student} - Mock {self.mock_number}"

    @staticmethod
    def get_grade(score):
        if score >= 85:
            return 1
        elif score >= 80:
            return 2
        elif score >= 75:
            return 3
        elif score >= 70:
            return 4
        elif score >= 60:
            return 5
        elif score >= 50:
            return 6
        elif score >= 45:
            return 7
        elif score >= 40:
            return 8
        else:
            return 9

    @staticmethod
    def get_grade_remark(grade):
        remarks = {
            1: "Highest",
            2: "Higher",
            3: "High",
            4: "High Average",
            5: "Average",
            6: "Low Average",
            7: "Low",
            8: "Lower",
            9: "Lowest",
        }
        return remarks.get(grade, '')

    def get_subjects(self):
        rows = []
        for field, label in self.SUBJECT_FIELDS:
            score = getattr(self, field)
            grade = self.get_grade(score)
            rows.append({
                "subject": label,
                "score": score,
                "grade": grade,
                "remark": self.get_grade_remark(grade),
            })
        return rows

    def get_aggregate(self):
        core = [self.get_grade(getattr(self, f)) for f in self.CORE_SUBJECTS]
        electives = sorted(
            self.get_grade(getattr(self, f))
            for f, _ in self.SUBJECT_FIELDS
            if f not in self.CORE_SUBJECTS
        )
        return sum(core) + sum(electives[:2])

    def get_total(self):
        return sum(getattr(self, field) for field, _ in self.SUBJECT_FIELDS)

    def get_average(self):
        return round(self.get_total() / len(self.SUBJECT_FIELDS), 2)

    def build_report(self):
        subjects = self.get_subjects()
        average = self.get_average()
        aggregate = self.get_aggregate()
        total = self.get_total()
        overall = "PASS" if average >= 50 else "FAIL"
        return {
            "student": self.student,
            "mock_number": self.mock_number,
            "subjects": subjects,
            "total": total,
            "average": average,
            "aggregate": aggregate,
            "overall_result": overall,
        }
