from django import forms
from .models import Student, Class, Dorm, Form


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
        # Filter classes and dorms by school
        self.fields['current_class'].queryset = Class.objects.filter(school=school)
        self.fields['dorm'].queryset          = Dorm.objects.filter(school=school)


class ClassForm(forms.ModelForm):
    class Meta:
        model  = Class
        fields = ['form', 'stream']

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['form'].queryset = Form.objects.filter(school=school)


class DormForm(forms.ModelForm):
    class Meta:
        model  = Dorm
        fields = ['name', 'capacity']


class FormLevelForm(forms.ModelForm):
    class Meta:
        model  = Form
        fields = ['name', 'order']