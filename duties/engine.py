"""
Duty Allocation Engine
Assigns ALL eligible students to duties every rotation.
Students are distributed fairly across duty areas.
"""
from .models import DutyArea, DutyAssignment, DutyHistory
from students.models import Student
from django.db import transaction
import math


def get_eligible_students(school, term):
    return list(Student.objects.filter(
        school=school,
        status=Student.STATUS_ACTIVE
    ).select_related('current_class', 'current_class__form', 'dorm'))


def get_history_counts(school, term, students):
    """
    Returns a dict: {student_id: {duty_area_id: count}}
    Used to prioritize students who have done fewer duties.
    """
    history = DutyHistory.objects.filter(
        school=school,
        term=term,
        student__in=students
    ).values('student_id', 'duty_area_id')

    counts = {}
    for h in history:
        sid  = h['student_id']
        did  = h['duty_area_id']
        if sid not in counts:
            counts[sid] = {}
        counts[sid][did] = counts[sid].get(did, 0) + 1
    return counts


@transaction.atomic
def allocate_duties(school, term, rotation, assigned_by):
    """
    Assigns ALL eligible students to duties.
    - Every student gets exactly one duty per rotation
    - Students are distributed fairly across areas
    - Specialization (form/dorm) is respected where possible
    - Students who have done fewer duties are prioritized
    """
    summary = {
        'assigned':         [],
        'warnings':         [],
        'unassigned_areas': [],
        'areas':            0,
    }

    # Clear existing assignments for this rotation
    DutyAssignment.objects.filter(
        school=school, term=term, rotation=rotation
    ).delete()
    DutyHistory.objects.filter(
        school=school, term=term, rotation=rotation
    ).delete()

    eligible_students = get_eligible_students(school, term)
    total_students    = len(eligible_students)

    if total_students == 0:
        summary['warnings'].append("No eligible students found.")
        return summary

    duty_areas = list(DutyArea.objects.filter(school=school, is_active=True))

    if not duty_areas:
        summary['warnings'].append("No active duty areas found.")
        return summary

    total_areas = len(duty_areas)

    # ── STEP 1: Calculate how many students each area gets ────
    # Base each area on its students_required, then scale up
    # so ALL students are assigned
    base_total = sum(a.students_required for a in duty_areas)

    # Build slot counts per area scaled to total students
    area_slots = {}
    if base_total == 0:
        # Equal distribution if no requirements set
        per_area = math.ceil(total_students / total_areas)
        for area in duty_areas:
            area_slots[area.id] = per_area
    else:
        # Scale proportionally so total slots >= total students
        scale = total_students / base_total
        assigned_slots = 0
        for i, area in enumerate(duty_areas):
            if i == len(duty_areas) - 1:
                # Last area gets remainder
                area_slots[area.id] = total_students - assigned_slots
            else:
                slots = max(1, round(area.students_required * scale))
                area_slots[area.id] = slots
                assigned_slots += slots

    # ── STEP 2: Get duty history for fair rotation ────────────
    history_counts = get_history_counts(school, term, eligible_students)

    # ── STEP 3: Sort students by total duty count (least first) ─
    def total_duty_count(student):
        return sum(history_counts.get(student.id, {}).values())

    eligible_students.sort(key=total_duty_count)

    # ── STEP 4: Build priority queues per area ────────────────
    # Each area gets a prioritized list of students
    area_queues = {}
    for area in duty_areas:
        candidates = eligible_students.copy()

        # Sort: prefer students who haven't done THIS area recently
        def area_priority(student):
            area_history = history_counts.get(student.id, {}).get(area.id, 0)
            total_history = total_duty_count(student)
            return (area_history, total_history)

        candidates.sort(key=area_priority)

        # Move specialization matches to front
        if area.specialization == 'form' and area.specific_form:
            priority = [s for s in candidates
                        if hasattr(s, 'current_class') and
                        s.current_class and
                        s.current_class.form == area.specific_form]
            others   = [s for s in candidates
                        if s not in priority]
            candidates = priority + others

        elif area.specialization == 'dorm' and area.specific_dorm:
            priority = [s for s in candidates if s.dorm == area.specific_dorm]
            others   = [s for s in candidates if s not in priority]
            candidates = priority + others

        elif area.specialization == 'class' and area.specific_class:
            priority = [s for s in candidates
                        if s.current_class == area.specific_class]
            others   = [s for s in candidates if s not in priority]
            candidates = priority + others

        area_queues[area.id] = candidates

    # ── STEP 5: Assign students to areas ─────────────────────
    assigned_student_ids = set()
    assignments_to_create = []
    history_to_create     = []

    for area in duty_areas:
        slots    = area_slots[area.id]
        queue    = area_queues[area.id]
        assigned = 0

        for student in queue:
            if assigned >= slots:
                break
            if student.id in assigned_student_ids:
                continue

            assignments_to_create.append(DutyAssignment(
                school      = school,
                term        = term,
                student     = student,
                duty_area   = area,
                rotation    = rotation,
                method      = 'auto',
                assigned_by = assigned_by,
            ))
            history_to_create.append(DutyHistory(
                school    = school,
                student   = student,
                duty_area = area,
                term      = term,
                rotation  = rotation,
            ))

            assigned_student_ids.add(student.id)
            assigned += 1
            summary['assigned'].append(f"{student} → {area}")

        if assigned < area.students_required:
            summary['warnings'].append(
                f"{area.name} needs {area.students_required}, got {assigned}."
            )

        summary['areas'] += 1

    # ── STEP 6: Handle any unassigned students ────────────────
    # (Can happen due to rounding — assign to areas with most capacity)
    unassigned = [s for s in eligible_students
                  if s.id not in assigned_student_ids]

    if unassigned:
        # Sort areas by current load (least loaded first)
        area_load = {a.id: 0 for a in duty_areas}
        for assignment in assignments_to_create:
            area_load[assignment.duty_area_id] += 1

        sorted_areas = sorted(duty_areas, key=lambda a: area_load[a.id])

        area_idx = 0
        for student in unassigned:
            area = sorted_areas[area_idx % len(sorted_areas)]
            assignments_to_create.append(DutyAssignment(
                school      = school,
                term        = term,
                student     = student,
                duty_area   = area,
                rotation    = rotation,
                method      = 'auto',
                assigned_by = assigned_by,
            ))
            history_to_create.append(DutyHistory(
                school    = school,
                student   = student,
                duty_area = area,
                term      = term,
                rotation  = rotation,
            ))
            assigned_student_ids.add(student.id)
            summary['assigned'].append(
                f"{student} → {area} (overflow)"
            )
            area_load[area.id] += 1
            area_idx += 1
            summary['warnings'].append(
                f"{student} assigned to {area} as overflow."
            )

    # ── STEP 7: Bulk save ─────────────────────────────────────
    DutyAssignment.objects.bulk_create(assignments_to_create)
    DutyHistory.objects.bulk_create(history_to_create)

    # Final check
    unassigned_final = [s for s in eligible_students
                        if s.id not in assigned_student_ids]
    for s in unassigned_final:
        summary['warnings'].append(f"⚠️ {s} was NOT assigned any duty!")

    return summary