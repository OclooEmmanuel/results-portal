from django.db import models

class Student(models.Model):
    full_name = models.CharField(max_length=100)
    index_number = models.CharField(max_length=20, unique=True)
    access_code = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="students/",blank=True, null=True)

    def __str__(self):
        return self.full_name
