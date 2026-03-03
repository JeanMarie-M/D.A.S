from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Student, Class, Dorm, Form
from .forms import StudentForm, ClassForm, DormForm, FormLevelForm


def get_school(request):
    """Helper — returns the school of the logged-in user"""
    return request.user.school


# ── STUDENT LIST ──────────────────────────────────────────
@login_required
def student_list(request):
    school   = get_school(request)
    students = Student.objects.filter(school=school).select_related('current_class', 'dorm')
    return render(request, 'students/list.html', {'students': students})


# ── STUDENT CREATE ─────────────────────────────────────────
@login_required
def student_create(request):
    school = get_school(request)
    form   = StudentForm(school, request.POST or None)
    if form.is_valid():
        student        = form.save(commit=False)
        student.school = school
        student.save()
        messages.success(request, f"Student {student.get_full_name()} added successfully.")
        return redirect('student_list')
    return render(request, 'students/form.html', {'form': form, 'title': 'Add Student'})


# ── STUDENT UPDATE ─────────────────────────────────────────
@login_required
def student_update(request, pk):
    school  = get_school(request)
    student = get_object_or_404(Student, pk=pk, school=school)
    form    = StudentForm(school, request.POST or None, instance=student)
    if form.is_valid():
        form.save()
        messages.success(request, "Student updated successfully.")
        return redirect('student_list')
    return render(request, 'students/form.html', {'form': form, 'title': 'Edit Student'})


# ── STUDENT DELETE ─────────────────────────────────────────
@login_required
def student_delete(request, pk):
    school  = get_school(request)
    student = get_object_or_404(Student, pk=pk, school=school)
    if request.method == 'POST':
        student.status = Student.STATUS_INACTIVE
        student.save()
        messages.success(request, "Student deactivated successfully.")
        return redirect('student_list')
    return render(request, 'students/confirm_delete.html', {'student': student})


# ── STUDENT DETAIL ─────────────────────────────────────────
@login_required
def student_detail(request, pk):
    school  = get_school(request)
    student = get_object_or_404(Student, pk=pk, school=school)
    history = student.class_history.all().order_by('-changed_at')
    return render(request, 'students/detail.html', {'student': student, 'history': history})