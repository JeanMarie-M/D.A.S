from django.db import models


class School(models.Model):
    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=20, unique=True)
    address     = models.TextField(blank=True)
    logo        = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    motto       = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True, blank=True, default='')
    phone       = models.CharField(max_length=20, blank=True)
    is_active   = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)

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

class SetupWizard(models.Model):
    """Tracks setup progress for each school"""
    school           = models.OneToOneField(School, on_delete=models.CASCADE, related_name='wizard')
    term_done        = models.BooleanField(default=False)
    forms_done       = models.BooleanField(default=False)
    classes_done     = models.BooleanField(default=False)
    dorms_done       = models.BooleanField(default=False)
    duty_areas_done  = models.BooleanField(default=False)
    students_done    = models.BooleanField(default=False)
    completed        = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def get_progress(self):
        steps = [
            self.term_done,
            self.forms_done,
            self.classes_done,
            self.dorms_done,
            self.duty_areas_done,
            self.students_done,
        ]
        done  = sum(steps)
        total = len(steps)
        return {
            'done':       done,
            'total':      total,
            'percentage': int((done / total) * 100),
        }

    def check_completed(self):
        self.completed = all([
            self.term_done,
            self.forms_done,
            self.classes_done,
            self.dorms_done,
            self.duty_areas_done,
            self.students_done,
        ])
        self.save()

    def __str__(self):
        return f"{self.school.name} — Setup Wizard"