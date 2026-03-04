from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from students.models import Student
from duties.models import DutyArea
from schools.models import Term


def login_view(request):
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
        error = "Invalid username or password."
    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    school = request.user.school
    context = {
        'total_students':   Student.objects.filter(school=school).count(),
        'eligible_students': Student.objects.filter(school=school, status='active').count(),
        'exempt_students':  Student.objects.filter(school=school).exclude(status='active').exclude(status='inactive').count(),
        'duty_areas':       DutyArea.objects.filter(school=school, is_active=True).count(),
        'current_term':     Term.objects.filter(school=school, is_current=True).first(),
    }
    return render(request, 'dashboard.html', context)