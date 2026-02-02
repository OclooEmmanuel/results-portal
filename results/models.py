from django.db import models

class Student(models.Model):
    full_name = models.CharField(max_length=100)
    index_number = models.CharField(max_length=20, unique=True)
    access_code = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="media/students/", blank=True, null=True)

    def __str__(self):
        return self.full_name




class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
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

"""  def total(self):
        return self.maths + self.english + self.science + self.rme + self.ict

    def average(self):
        return self.total() / 5

    def __str__(self):
        return f"{self.student}'s mock {self.mock_number} Result"
"""
