from django.db import models
from schools.models import School


class Form(models.Model):
    """Form level e.g. Form 1, Form 2, Form 3, Form 4"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='forms')
    name   = models.CharField(max_length=20)  # e.g. "Form 1"
    order  = models.PositiveIntegerField(default=1)  # for sorting

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['order']

    def __str__(self):
        return f"{self.school.code} — {self.name}"


class Class(models.Model):
    """Specific stream e.g. Form 1K, Form 2E"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    form   = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='classes')
    stream = models.CharField(max_length=10)  # e.g. "K", "E", "N"

    class Meta:
        unique_together = ('school', 'form', 'stream')
        ordering = ['form__order', 'stream']

    def __str__(self):
        return f"{self.form.name}{self.stream}"  # e.g. Form 1K


class Dorm(models.Model):
    """Dormitory e.g. Kibaki Dorm, Uhuru Dorm"""
    school   = models.ForeignKey(School, on_delete=models.CASCADE, related_name='dorms')
    name     = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.school.code})"


class Student(models.Model):
    """Core student profile"""

    # Eligibility status choices
    STATUS_ACTIVE   = 'active'
    STATUS_PREFECT  = 'prefect'
    STATUS_MEDICAL  = 'medical'
    STATUS_ABSENT   = 'absent'
    STATUS_INACTIVE = 'inactive'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,   'Active'),
        (STATUS_PREFECT,  'Prefect'),
        (STATUS_MEDICAL,  'Medical Exemption'),
        (STATUS_ABSENT,   'Absent'),
        (STATUS_INACTIVE, 'Inactive / Left School'),
    ]

    school           = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    admission_number = models.CharField(max_length=20)
    first_name       = models.CharField(max_length=50)
    last_name        = models.CharField(max_length=50)
    current_class    = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    dorm             = models.ForeignKey(Dorm, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    date_admitted    = models.DateField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    medical_note     = models.TextField(blank=True)  # filled if status = medical
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school', 'admission_number')
        ordering = ['current_class__form__order', 'last_name']

    def __str__(self):
        return f"{self.admission_number} — {self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_eligible_for_duty(self):
        """Core eligibility rule — used by allocation engine"""
        return self.status == self.STATUS_ACTIVE

    @property
    def form(self):
        """Shortcut to get the student's form"""
        return self.current_class.form if self.current_class else None


class ClassHistory(models.Model):
    """Tracks class & dorm changes as student is promoted"""
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='class_history')
    old_class  = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='+')
    new_class  = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='+')
    old_dorm   = models.ForeignKey(Dorm, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    new_dorm   = models.ForeignKey(Dorm, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason     = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} promoted on {self.changed_at.date()}"
