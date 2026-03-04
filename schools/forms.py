from django import forms
from .models import School, Term
from accounts.models import User


def add_bootstrap(form):
    for field in form.fields.values():
        if hasattr(field.widget, 'attrs'):
            existing = field.widget.attrs.get('class', '')
            if 'form-control' not in existing and 'form-select' not in existing:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
    return form


class SchoolRegistrationForm(forms.Form):
    """
    One form that registers both the school and its first admin user.
    """
    # School details
    school_name  = forms.CharField(max_length=200, label="School Name")
    school_code  = forms.CharField(max_length=20,  label="School Code (unique)")
    school_email = forms.EmailField(label="School Email")
    school_phone = forms.CharField(max_length=20, required=False, label="Phone")
    address      = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    motto        = forms.CharField(max_length=200, required=False)

    # Admin account
    admin_username  = forms.CharField(max_length=50,  label="Admin Username")
    admin_first_name = forms.CharField(max_length=50, label="First Name")
    admin_last_name  = forms.CharField(max_length=50, label="Last Name")
    admin_email      = forms.EmailField(label="Admin Email")
    admin_password   = forms.CharField(
        widget=forms.PasswordInput, label="Password"
    )
    admin_password2  = forms.CharField(
        widget=forms.PasswordInput, label="Confirm Password"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)

    def clean_school_code(self):
        code = self.cleaned_data['school_code'].upper()
        if School.objects.filter(code=code).exists():
            raise forms.ValidationError("This school code is already taken.")
        return code

    def clean_school_email(self):
        email = self.cleaned_data['school_email']
        if School.objects.filter(email=email).exists():
            raise forms.ValidationError("A school with this email already exists.")
        return email

    def clean_admin_username(self):
        username = self.cleaned_data['admin_username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('admin_password')
        p2 = cleaned.get('admin_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class TermForm(forms.ModelForm):
    class Meta:
        model  = Term
        fields = ['name', 'start_date', 'end_date', 'rotation_period', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)