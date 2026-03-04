from django import forms
from .models import Student, Class, Dorm, Form


def add_bootstrap(form):
    """Adds Bootstrap form-control class to all form fields"""
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            existing = field.widget.attrs.get('class', '')
            if 'form-control' not in existing and 'form-select' not in existing:
                # Use form-select for dropdowns, form-control for everything else
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
    return form


class StudentForm(forms.ModelForm):
    class Meta:
        model  = Student
        fields = [
            'admission_number', 'first_name', 'last_name',
            'current_class', 'dorm', 'date_admitted',
            'status', 'medical_note'
        ]
        widgets = {
            'date_admitted': forms.DateInput(attrs={'type': 'date'}),
            'medical_note':  forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_class'].queryset = Class.objects.filter(school=school)
        self.fields['dorm'].queryset          = Dorm.objects.filter(school=school)
        add_bootstrap(self)  # ← applies Bootstrap classes


class ClassForm(forms.ModelForm):
    class Meta:
        model  = Class
        fields = ['form', 'stream']

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['form'].queryset = Form.objects.filter(school=school)
        add_bootstrap(self)


class DormForm(forms.ModelForm):
    class Meta:
        model  = Dorm
        fields = ['name', 'capacity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


class FormLevelForm(forms.ModelForm):
    class Meta:
        model  = Form
        fields = ['name', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)