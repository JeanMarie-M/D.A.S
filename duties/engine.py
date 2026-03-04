"""
Duty Allocation Engine
Core logic for assigning duties to students fairly and correctly.
"""
from .models import DutyArea, DutyAssignment, DutyHistory
from students.models import Student
from django.db import transaction


def get_eligible_students(school, term):
    """Returns all students eligible for duty allocation"""
    return Student.objects.filter(
        school=school,
        status=Student.STATUS_ACTIVE
    ).select_related('current_class', 'current_class__form', 'dorm')


def get_duty_history(school, term, student):
    """Returns list of duty area IDs student has had this term"""
    return list(
        DutyHistory.objects.filter(
            school=school,
            term=term,
            student=student
        ).values_list('duty_area_id', flat=True)
    )


def get_candidate_students(duty_area, eligible_students, assigned_ids):
    """
    Returns ordered list of candidate students for a duty area.
    Priority:
      1. Same class as duty area specialization
      2. Same form
      3. Same dorm
      4. Any eligible student
    Excludes already assigned students.
    """
    available = [s for s in eligible_students if s.id not in assigned_ids]

    if duty_area.specialization == 'class' and duty_area.specific_class:
        priority = [s for s in available if s.current_class == duty_area.specific_class]
        fallback = [s for s in available if s.current_class != duty_area.specific_class]
        return priority + fallback

    elif duty_area.specialization == 'form' and duty_area.specific_form:
        priority = [s for s in available if s.form == duty_area.specific_form]
        fallback = [s for s in available if s.form != duty_area.specific_form]
        return priority + fallback

    elif duty_area.specialization == 'dorm' and duty_area.specific_dorm:
        priority = [s for s in available if s.dorm == duty_area.specific_dorm]
        fallback = [s for s in available if s.dorm != duty_area.specific_dorm]
        return priority + fallback

    return available


def sort_by_duty_history(candidates, school, term):
    """
    Sort candidates so students with LEAST duty history come first.
    This ensures fair rotation — no student repeats a duty
    before others have had it.
    """
    def history_count(student):
        return DutyHistory.objects.filter(
            school=school,
            term=term,
            student=student
        ).count()

    return sorted(candidates, key=history_count)


@transaction.atomic
def allocate_duties(school, term, rotation, assigned_by):
    """
    Main allocation function.
    Assigns all duty areas for a given rotation period.
    Returns a summary dict with results and any warnings.
    """
    summary = {
        'assigned':  [],
        'warnings':  [],
        'unassigned_areas': [],
    }

    # Clear existing assignments for this rotation
    DutyAssignment.objects.filter(
        school=school,
        term=term,
        rotation=rotation
    ).delete()

    eligible_students = list(get_eligible_students(school, term))
    duty_areas        = DutyArea.objects.filter(school=school, is_active=True)
    assigned_ids      = set()  # tracks students already assigned this rotation

    for area in duty_areas:
        # Get candidates for this duty area
        candidates = get_candidate_students(area, eligible_students, assigned_ids)

        # Sort by least duty history first (fairness rotation)
        candidates = sort_by_duty_history(candidates, school, term)

        # Filter out students who already had THIS specific duty this term
        fresh_candidates = [
            s for s in candidates
            if area.id not in get_duty_history(school, term, s)
        ]

        # Fallback to any candidate if all have had this duty
        if not fresh_candidates:
            fresh_candidates = candidates
            summary['warnings'].append(
                f"All eligible students have had '{area}' before. Repeating."
            )

        # Assign required number of students
        assigned_count = 0
        for student in fresh_candidates:
            if assigned_count >= area.students_required:
                break
            if student.id in assigned_ids:
                continue

            # Create assignment
            DutyAssignment.objects.create(
                school=school,
                term=term,
                student=student,
                duty_area=area,
                rotation=rotation,
                method='auto',
                assigned_by=assigned_by,
            )

            # Record in history
            DutyHistory.objects.create(
                school=school,
                student=student,
                duty_area=area,
                term=term,
                rotation=rotation,
            )

            assigned_ids.add(student.id)
            assigned_count += 1
            summary['assigned'].append(f"{student} → {area}")

        if assigned_count < area.students_required:
            summary['unassigned_areas'].append(
                f"{area} needs {area.students_required}, got {assigned_count}"
            )

    # Warn about students who were not assigned any duty
    unassigned_students = [
        s for s in eligible_students if s.id not in assigned_ids
    ]
    for s in unassigned_students:
        summary['warnings'].append(f"{s} was NOT assigned any duty.")

    return summary