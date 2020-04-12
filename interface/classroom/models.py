from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
import string


class FSUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_of = models.ManyToManyField("Classroom", related_name="student", blank=True)
    teacher_of = models.ManyToManyField("Classroom", related_name="teacher", blank=True)
    current_class_ide = models.CharField(max_length=6, blank=True, null=True)
    current_port = models.IntegerField(blank=True, null=True)


class Classroom(models.Model):
    classroom_code = models.CharField(max_length=6, blank=True, null=True)
    classroom_name = models.CharField(max_length=100)
    description = models.TextField()
    JAVA, PYTHON, CPP = "J", "P", "C"
    env = models.CharField(max_length=1, choices=[(JAVA, "Java"), (PYTHON, "Python3"), (CPP, "C++")])
    teacher_code = models.CharField(max_length=50)

    def generate_code(self):
        self.classroom_code = get_random_string(length=6, allowed_chars=string.ascii_uppercase)
        return self.classroom_code


class DockerInstances(models.Model):
    port = models.IntegerField()


class Submission(models.Model):
    user = models.ForeignKey(FSUser, on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True)

class Assignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    workspace_template = models.FileField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    folder_name = models.CharField(max_length=200)
    submitted_by = models.ManyToManyField(Submission)
