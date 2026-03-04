from django.db import models
from schools.models import School, Term
from students.models import Student, Class, Dorm, Form


class DutyArea(models.Model):
    """A specific location/area where duty is performed"""

    SIZE_CHOICES = [
        ('small',  'Small'),
        ('medium', 'Medium'),
        ('large',  'Large'),
    ]

    SPECIALIZATION_CHOICES = [
        ('none',     'None'),
        ('class',    'Class Based'),
        ('dorm',     'Dorm Based'),
        ('form',     'Form Based'),
        ('subject',  'Subject Based'),
    ]

    school          = models.ForeignKey(School, on_delete=models.CASCADE, related_name='duty_areas')
    name            = models.CharField(max_length=100)   # e.g. "Block A Corridor"
    label           = models.CharField(max_length=50)    # e.g. "A1", "D3"
    description     = models.TextField(blank=True)
    area_size       = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    is_heavy        = models.BooleanField(default=False)
    tools_required  = models.TextField(blank=True)       # e.g. "mop, bucket, broom"
    specialization  = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, default='none')

    # Specialization targets (only one will be used based on specialization field)
    specific_class  = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    specific_dorm   = models.ForeignKey(Dorm,  on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    specific_form   = models.ForeignKey(Form,  on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    specific_subject = models.CharField(max_length=100, blank=True)

    # How many students needed for this duty
    students_required = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'label')
        ordering = ['label']

    def __str__(self):
        return f"{self.label} — {self.name}"


class DutyAssignment(models.Model):
    """A single student assigned to a duty area for a specific period"""

    ASSIGN_METHOD = [
        ('auto',   'Auto Assigned'),
        ('manual', 'Manually Assigned'),
        ('swap',   'Swap'),
    ]

    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name='assignments')
    term        = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='assignments')
    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    duty_area   = models.ForeignKey(DutyArea, on_delete=models.CASCADE, related_name='assignments')
    rotation    = models.PositiveIntegerField(default=1)  # rotation number within term
    method      = models.CharField(max_length=10, choices=ASSIGN_METHOD, default='auto')
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        unique_together = ('term', 'student', 'rotation')  # one duty per student per rotation
        ordering = ['duty_area__label', 'student__last_name']

    def __str__(self):
        return f"{self.student} → {self.duty_area} (Rotation {self.rotation})"


class DutySwapRequest(models.Model):
    """Manual swap request between two students"""

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    school         = models.ForeignKey(School, on_delete=models.CASCADE, related_name='swap_requests')
    term           = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='swap_requests')
    rotation       = models.PositiveIntegerField()
    from_student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='swap_from')
    to_student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='swap_to')
    from_duty      = models.ForeignKey(DutyArea, on_delete=models.CASCADE, related_name='swap_from')
    to_duty        = models.ForeignKey(DutyArea, on_delete=models.CASCADE, related_name='swap_to')
    reason         = models.TextField()
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='swap_requested')
    reviewed_by    = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,)

class DutyHistory(models.Model):
    """Tracks every duty a student has ever had — used for rotation fairness"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='duty_history')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='duty_history')
    duty_area = models.ForeignKey(DutyArea, on_delete=models.CASCADE, related_name='duty_history')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='duty_history')
    rotation = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} had {self.duty_area} — Rotation {self.rotation}"