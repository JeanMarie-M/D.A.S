from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import SetupWizard, Term
from students.models import Form, Class, Dorm, Student
from duties.models import DutyArea
from .forms import TermForm
from students.forms import StudentForm, ClassForm, DormForm, FormLevelForm
from duties.forms import DutyAreaForm
from students.imports import import_students_from_xlsx, import_students_from_csv


def get_or_create_wizard(school):
    wizard, _ = SetupWizard.objects.get_or_create(school=school)
    return wizard


def get_school(request):
    return request.user.school


# ── WIZARD HOME ───────────────────────────────────────────
@login_required
def wizard_home(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)

    # If already completed redirect to dashboard
    if wizard.completed:
        messages.success(request, "Setup already completed!")
        return redirect('dashboard')

    steps = [
        {
            'number':  1,
            'name':    'Create Term',
            'desc':    'Set up your school term and rotation period.',
            'icon':    'bi-calendar3',
            'done':    wizard.term_done,
            'url':     'wizard_term',
        },
        {
            'number':  2,
            'name':    'Add Forms',
            'desc':    'Add form levels e.g. Form 1, Form 2, Form 3, Form 4.',
            'icon':    'bi-layers',
            'done':    wizard.forms_done,
            'url':     'wizard_forms',
        },
        {
            'number':  3,
            'name':    'Add Classes',
            'desc':    'Add class streams e.g. Form 1K, Form 2E.',
            'icon':    'bi-journal-text',
            'done':    wizard.classes_done,
            'url':     'wizard_classes',
        },
        {
            'number':  4,
            'name':    'Add Dorms',
            'desc':    'Add dormitories e.g. Kibaki Dorm, Uhuru Dorm.',
            'icon':    'bi-house',
            'done':    wizard.dorms_done,
            'url':     'wizard_dorms',
        },
        {
            'number':  5,
            'name':    'Add Duty Areas',
            'desc':    'Add areas where duties will be performed.',
            'icon':    'bi-map',
            'done':    wizard.duty_areas_done,
            'url':     'wizard_duty_areas',
        },
        {
            'number':  6,
            'name':    'Add Students',
            'desc':    'Add students manually or import from Excel/CSV.',
            'icon':    'bi-people',
            'done':    wizard.students_done,
            'url':     'wizard_students',
        },
    ]

    progress = wizard.get_progress()
    return render(request, 'wizard/home.html', {
        'wizard':   wizard,
        'steps':    steps,
        'progress': progress,
        'school':   school,
    })


# ── STEP 1: TERM ──────────────────────────────────────────
@login_required
def wizard_term(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)
    form   = TermForm(request.POST or None)

    if form.is_valid():
        term        = form.save(commit=False)
        term.school = school
        if term.is_current:
            Term.objects.filter(school=school).update(is_current=False)
        term.save()
        wizard.term_done = True
        wizard.save()
        messages.success(request, "✅ Term created successfully!")
        return redirect('wizard_forms')

    existing = Term.objects.filter(school=school)
    return render(request, 'wizard/step_term.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'step':     1,
    })


# ── STEP 2: FORMS ─────────────────────────────────────────
@login_required
def wizard_forms(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)
    form   = FormLevelForm(request.POST or None)

    if form.is_valid():
        f        = form.save(commit=False)
        f.school = school
        f.save()
        wizard.forms_done = True
        wizard.save()
        messages.success(request, f"✅ {f.name} added!")
        return redirect('wizard_forms')

    if 'next' in request.GET:
        if Form.objects.filter(school=school).exists():
            return redirect('wizard_classes')
        else:
            messages.error(request, "Add at least one form before continuing.")

    existing = Form.objects.filter(school=school).order_by('order')
    return render(request, 'wizard/step_forms.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'step':     2,
    })


# ── STEP 3: CLASSES ───────────────────────────────────────
@login_required
def wizard_classes(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)
    form   = ClassForm(school, request.POST or None)

    if form.is_valid():
        c        = form.save(commit=False)
        c.school = school
        c.save()
        wizard.classes_done = True
        wizard.save()
        messages.success(request, f"✅ {c} added!")
        return redirect('wizard_classes')

    if 'next' in request.GET:
        if Class.objects.filter(school=school).exists():
            return redirect('wizard_dorms')
        else:
            messages.error(request, "Add at least one class before continuing.")

    existing = Class.objects.filter(school=school).select_related('form')
    return render(request, 'wizard/step_classes.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'step':     3,
    })


# ── STEP 4: DORMS ─────────────────────────────────────────
@login_required
def wizard_dorms(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)
    form   = DormForm(request.POST or None)

    if form.is_valid():
        d        = form.save(commit=False)
        d.school = school
        d.save()
        wizard.dorms_done = True
        wizard.save()
        messages.success(request, f"✅ {d.name} added!")
        return redirect('wizard_dorms')

    if 'next' in request.GET:
        if Dorm.objects.filter(school=school).exists():
            return redirect('wizard_duty_areas')
        else:
            messages.error(request, "Add at least one dorm before continuing.")

    existing = Dorm.objects.filter(school=school)
    return render(request, 'wizard/step_dorms.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'step':     4,
    })


# ── STEP 5: DUTY AREAS ────────────────────────────────────
@login_required
def wizard_duty_areas(request):
    school = get_school(request)
    wizard = get_or_create_wizard(school)
    form   = DutyAreaForm(school, request.POST or None)

    if form.is_valid():
        area        = form.save(commit=False)
        area.school = school
        area.save()
        wizard.duty_areas_done = True
        wizard.save()
        messages.success(request, f"✅ {area.name} added!")
        return redirect('wizard_duty_areas')

    if 'next' in request.GET:
        if DutyArea.objects.filter(school=school).exists():
            return redirect('wizard_students')
        else:
            messages.error(request, "Add at least one duty area before continuing.")

    existing = DutyArea.objects.filter(school=school)
    return render(request, 'wizard/step_duty_areas.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'step':     5,
    })


# ── STEP 6: STUDENTS ──────────────────────────────────────
@login_required
def wizard_students(request):
    school  = get_school(request)
    wizard  = get_or_create_wizard(school)
    form    = StudentForm(school, request.POST or None)
    result  = None

    # Handle Excel/CSV import
    if request.method == 'POST' and request.FILES.get('import_file'):
        file     = request.FILES['import_file']
        filename = file.name.lower()
        if filename.endswith('.xlsx'):
            result = import_students_from_xlsx(file, school)
        elif filename.endswith('.csv'):
            result = import_students_from_csv(file, school)

        if result and (result['success'] or result['updated']):
            wizard.students_done = True
            wizard.check_completed()
            messages.success(
                request,
                f"✅ {result['success']} students imported, "
                f"{result['updated']} updated."
            )

    # Handle manual add
    elif request.method == 'POST':
        if form.is_valid():
            student        = form.save(commit=False)
            student.school = school
            student.save()
            wizard.students_done = True
            wizard.check_completed()
            messages.success(
                request,
                f"✅ {student.get_full_name()} added!"
            )
            return redirect('wizard_students')

    if 'finish' in request.GET:
        if Student.objects.filter(school=school).exists():
            wizard.students_done = True
            wizard.check_completed()
            messages.success(
                request,
                "🎉 Setup complete! You can now allocate duties."
            )
            return redirect('dashboard')
        else:
            messages.error(request, "Add at least one student before finishing.")

    existing = Student.objects.filter(
        school=school
    ).select_related('current_class', 'dorm')[:10]

    return render(request, 'wizard/step_students.html', {
        'form':     form,
        'existing': existing,
        'wizard':   wizard,
        'result':   result,
        'step':     6,
    })