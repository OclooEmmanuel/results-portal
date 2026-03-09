from django.db import models

class Student(models.Model):
    full_name = models.CharField(max_length=100)
    index_number = models.CharField(max_length=20, unique=True)
    access_code = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="students/", blank=True, null=True)

    def __str__(self):
        return self.full_name




class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
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


    def get_grade( score):
        """
        Grade Scale (1-9)
        """
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


    def get_grade_remark(grade):
        """
        Official Interpretation
        """
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
        return remarks.get(grade,'')


