
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    ROLES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'School Admin'),
        ('prefect', 'Prefect'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='prefect')
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users'
    )

    def is_school_admin(self):
        return self.role in ['admin', 'superadmin']

    def is_prefect(self):
        return self.role == 'prefect'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"





