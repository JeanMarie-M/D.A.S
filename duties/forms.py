from django import forms
from .models import DutyArea, DutyAssignment, DutySwapRequest
from students.models import Class, Dorm, Form


def add_bootstrap(form):
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            existing = field.widget.attrs.get('class', '')
            if 'form-control' not in existing and 'form-select' not in existing:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
    return form


class DutyAreaForm(forms.ModelForm):
    class Meta:
        model  = DutyArea
        fields = [
            'name', 'label', 'description',
            'area_size', 'is_heavy', 'tools_required',
            'specialization', 'specific_class',
            'specific_dorm', 'specific_form', 'specific_subject',
            'students_required',
        ]
        widgets = {
            'description':    forms.Textarea(attrs={'rows': 2}),
            'tools_required': forms.TextInput(attrs={'placeholder': 'e.g. mop, broom, bucket'}),
        }

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specific_class'].queryset = Class.objects.filter(school=school)
        self.fields['specific_dorm'].queryset  = Dorm.objects.filter(school=school)
        self.fields['specific_form'].queryset  = Form.objects.filter(school=school)
        add_bootstrap(self)


class ManualAssignForm(forms.ModelForm):
    class Meta:
        model  = DutyAssignment
        fields = ['student', 'duty_area', 'rotation']

    def __init__(self, school, term, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from students.models import Student
        self.fields['student'].queryset   = Student.objects.filter(
            school=school, status=Student.STATUS_ACTIVE
        )
        self.fields['duty_area'].queryset = DutyArea.objects.filter(
            school=school, is_active=True
        )
        add_bootstrap(self)


class SwapRequestForm(forms.ModelForm):
    class Meta:
        model  = DutySwapRequest
        fields = ['from_student', 'to_student', 'from_duty', 'to_duty', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, school, term, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from students.models import Student
        students = Student.objects.filter(school=school, status=Student.STATUS_ACTIVE)
        areas    = DutyArea.objects.filter(school=school, is_active=True)
        self.fields['from_student'].queryset = students
        self.fields['to_student'].queryset   = students
        self.fields['from_duty'].queryset    = areas
        self.fields['to_duty'].queryset      = areas
        add_bootstrap(self)