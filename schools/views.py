from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import School, Term
from .forms import SchoolRegistrationForm, TermForm
from accounts.models import User


def get_school(request):
    return request.user.school


# ── SCHOOL REGISTRATION ───────────────────────────────────
def school_register(request,):
    # If already logged in go to dashboard
    if request.user.is_authenticated:
        messages.success(
            request,
            f"School '{school.name}' registered! "
            f"Login to complete your setup."
        )
        return redirect('login')

    form = SchoolRegistrationForm(request.POST or None)

    if form.is_valid():
        try:
            with transaction.atomic():
                # Create school
                school = School.objects.create(
                    name    = form.cleaned_data['school_name'],
                    code    = form.cleaned_data['school_code'],
                    email   = form.cleaned_data['school_email'],
                    phone   = form.cleaned_data['school_phone'],
                    address = form.cleaned_data['address'],
                    motto   = form.cleaned_data['motto'],
                )

                # Create admin user for this school
                User.objects.create_user(
                    username   = form.cleaned_data['admin_username'],
                    email      = form.cleaned_data['admin_email'],
                    password   = form.cleaned_data['admin_password'],
                    first_name = form.cleaned_data['admin_first_name'],
                    last_name  = form.cleaned_data['admin_last_name'],
                    role       = 'admin',
                    school     = school,
                )

                messages.success(
                    request,
                    f"School '{school.name}' registered! Login with your admin credentials."
                )
                return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration failed: {e}")

    return render(request, 'schools/register.html', {'form': form})

# ── TERM LIST ─────────────────────────────────────────────
@login_required
def term_list(request):
    school = get_school(request)
    terms  = Term.objects.filter(school=school).order_by('-start_date')
    return render(request, 'schools/term_list.html', {'terms': terms})


# ── TERM CREATE ───────────────────────────────────────────
@login_required
def term_create(request):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can create terms.")
        return redirect('term_list')

    school = get_school(request)
    form   = TermForm(request.POST or None)

    if form.is_valid():
        term = form.save(commit=False)
        term.school = school
        if term.is_current:
            Term.objects.filter(school=school).update(is_current=False)
        term.save()
        messages.success(request, f"Term '{term.name}' created.")
        return redirect('term_list')

    return render(request, 'schools/term_form.html', {'form': form, 'title': 'Add Term'})


# ── TERM UPDATE ───────────────────────────────────────────
@login_required
def term_update(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can edit terms.")
        return redirect('term_list')

    school = get_school(request)
    term   = get_object_or_404(Term, pk=pk, school=school)
    form   = TermForm(request.POST or None, instance=term)

    if form.is_valid():
        updated = form.save(commit=False)
        if updated.is_current:
            Term.objects.filter(school=school).exclude(pk=pk).update(is_current=False)
        updated.save()
        messages.success(request, f"Term '{term.name}' updated.")
        return redirect('term_list')

    return render(request, 'schools/term_form.html', {'form': form, 'title': 'Edit Term'})


# ── SET CURRENT TERM ──────────────────────────────────────
@login_required
def term_set_current(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can change the current term.")
        return redirect('term_list')

    school = get_school(request)
    term   = get_object_or_404(Term, pk=pk, school=school)
    Term.objects.filter(school=school).update(is_current=False)
    term.is_current = True
    term.save()
    messages.success(request, f"'{term.name}' is now the current term.")
    return redirect('term_list')


# ── TERM DELETE ───────────────────────────────────────────
@login_required
def term_delete(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can delete terms.")
        return redirect('term_list')

    school = get_school(request)
    term   = get_object_or_404(Term, pk=pk, school=school)

    if request.method == 'POST':
        term.delete()
        messages.success(request, "Term deleted.")
        return redirect('term_list')

    return render(request, 'schools/term_confirm_delete.html', {'term': term})


# ── SCHOOL PROFILE ────────────────────────────────────────
@login_required
def school_profile(request):
    school = get_school(request)
    return render(request, 'schools/profile.html', {'school': school})