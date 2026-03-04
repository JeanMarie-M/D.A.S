from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from duties.models import DutyAssignment
from students.models import Class, Dorm
from duties.models import DutyArea
from schools.models import Term


def get_school(request):
    return request.user.school


@login_required
def report_full_school(request):
    school  = get_school(request)
    term    = Term.objects.filter(school=school, is_current=True).first()
    roster  = DutyAssignment.objects.filter(
        school=school, term=term, is_active=True
    ).select_related(
        'student', 'duty_area',
        'student__current_class',
        'student__current_class__form',
        'student__dorm'
    ).order_by('student__current_class__form__order', 'student__last_name')
    return render(request, 'reports/full_school.html', {'roster': roster, 'term': term})


@login_required
def report_by_class(request):
    school  = get_school(request)
    term    = Term.objects.filter(school=school, is_current=True).first()
    classes = Class.objects.filter(school=school)
    selected_class = request.GET.get('class_id')
    roster  = DutyAssignment.objects.filter(
        school=school, term=term,
        student__current_class_id=selected_class,
        is_active=True
    ).select_related('student', 'duty_area') if selected_class else []
    return render(request, 'reports/by_class.html', {
        'roster': roster, 'term': term,
        'classes': classes, 'selected_class': selected_class
    })


@login_required
def report_by_dorm(request):
    school   = get_school(request)
    term     = Term.objects.filter(school=school, is_current=True).first()
    dorms    = Dorm.objects.filter(school=school)
    selected_dorm = request.GET.get('dorm_id')
    roster   = DutyAssignment.objects.filter(
        school=school, term=term,
        student__dorm_id=selected_dorm,
        is_active=True
    ).select_related('student', 'duty_area') if selected_dorm else []
    return render(request, 'reports/by_dorm.html', {
        'roster': roster, 'term': term,
        'dorms': dorms, 'selected_dorm': selected_dorm
    })


@login_required
def report_by_area(request):
    school   = get_school(request)
    term     = Term.objects.filter(school=school, is_current=True).first()
    areas    = DutyArea.objects.filter(school=school, is_active=True)
    selected_area = request.GET.get('area_id')
    roster   = DutyAssignment.objects.filter(
        school=school, term=term,
        duty_area_id=selected_area,
        is_active=True
    ).select_related('student', 'duty_area') if selected_area else []
    return render(request, 'reports/by_area.html', {
        'roster': roster, 'term': term,
        'areas': areas, 'selected_area': selected_area
    })