from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            if user.school:
                from schools.models import SetupWizard
                wizard, _ = SetupWizard.objects.get_or_create(school=user.school)
                if not wizard.completed:
                    return redirect('wizard_home')
            return redirect('dashboard')
        error = "Invalid username or password."
    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    school = request.user.school

    if not school:
        messages.error(request, "Your account is not linked to any school.")
        return render(request, 'dashboard.html', {})

    from students.models import Student
    from duties.models import DutyArea
    from schools.models import Term, SetupWizard

    current_term = Term.objects.filter(school=school, is_current=True).first()

    if not current_term and request.user.is_school_admin():
        messages.warning(
            request,
            '⚠️ No active term set. '
            '<a href="/schools/terms/add/" class="alert-link">'
            'Create your first term here</a> before allocating duties.'
        )

    wizard, _ = SetupWizard.objects.get_or_create(school=school)

    context = {
        'total_students':    Student.objects.filter(school=school).count(),
        'eligible_students': Student.objects.filter(school=school, status='active').count(),
        'exempt_students':   Student.objects.filter(
                                school=school
                             ).exclude(status='active').exclude(status='inactive').count(),
        'duty_areas':        DutyArea.objects.filter(school=school, is_active=True).count(),
        'current_term':      current_term,
        'wizard_complete':   wizard.completed,
        'wizard_progress':   wizard.get_progress(),
    }
    return render(request, 'dashboard.html', context)


# ── USER LIST ─────────────────────────────────────────────
@login_required
def user_list(request):
    if not request.user.is_school_admin():
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    school = request.user.school
    users  = User.objects.filter(school=school).order_by('role', 'first_name')
    return render(request, 'accounts/user_list.html', {'users': users})


# ── USER CREATE ───────────────────────────────────────────
@login_required
def user_create(request):
    if not request.user.is_school_admin():
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    school = request.user.school

    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        role       = request.POST.get('role', 'prefect')
        password   = request.POST.get('password', '').strip()
        password2  = request.POST.get('password2', '').strip()

        errors = []

        if not username:
            errors.append("Username is required.")
        elif User.objects.filter(username=username).exists():
            errors.append("Username already taken.")

        if not password:
            errors.append("Password is required.")
        elif password != password2:
            errors.append("Passwords do not match.")

        if not first_name or not last_name:
            errors.append("Full name is required.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            User.objects.create_user(
                username   = username,
                first_name = first_name,
                last_name  = last_name,
                email      = email,
                password   = password,
                role       = role,
                school     = school,
            )
            messages.success(
                request,
                f"User '{username}' created as {role}."
            )
            return redirect('user_list')

    return render(request, 'accounts/user_form.html', {'title': 'Add User'})


# ── USER EDIT ─────────────────────────────────────────────
@login_required
def user_update(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    school = request.user.school
    user   = get_object_or_404(User, pk=pk, school=school)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.role       = request.POST.get('role', user.role)

        # Change password only if provided
        new_password = request.POST.get('password', '').strip()
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f"User '{user.username}' updated.")
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'title': 'Edit User',
        'edit_user': user,
    })


# ── USER DELETE ───────────────────────────────────────────
@login_required
def user_delete(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    school = request.user.school
    user   = get_object_or_404(User, pk=pk, school=school)

    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted.")
        return redirect('user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'del_user': user})


# ── CHANGE OWN PASSWORD ───────────────────────────────────
@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm      = request.POST.get('confirm', '')

        if not request.user.check_password(old_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm:
            messages.error(request, "New passwords do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Password changed. Please login again.")
            return redirect('login')

    return render(request, 'accounts/change_password.html')