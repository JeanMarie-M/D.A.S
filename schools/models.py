from django.db import models

# Create your models here.
class School(models.Model):
    name       = models.CharField(max_length=200)
    code       = models.CharField(max_length=20, unique=True)
    address    = models.TextField(blank=True)
    logo       = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    motto      = models.CharField(max_length=200, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Term(models.Model):
    ROTATION_CHOICES = [
        ('daily',    'Daily'),
        ('weekly',   'Weekly'),
        ('biweekly', 'Every 2 Weeks'),
        ('monthly',  'Monthly'),
    ]
    school          = models.ForeignKey(School, on_delete=models.CASCADE, related_name='terms')
    name            = models.CharField(max_length=50)
    start_date      = models.DateField()
    end_date        = models.DateField()
    is_current      = models.BooleanField(default=False)
    rotation_period = models.CharField(max_length=20, choices=ROTATION_CHOICES, default='weekly')

    def __str__(self):
        return f"{self.school.name} — {self.name}"