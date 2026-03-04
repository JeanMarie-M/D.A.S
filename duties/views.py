from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import DutyArea, DutyAssignment, DutySwapRequest
from .forms import DutyAreaForm, ManualAssignForm, SwapRequestForm
from .engine import allocate_duties
from schools.models import Term


def get_school(request):
    return request.user.school


# ── DUTY AREAS ────────────────────────────────────────────
@login_required
def duty_area_list(request):
    school = get_school(request)
    areas  = DutyArea.objects.filter(school=school, is_active=True)
    return render(request, 'duties/area_list.html', {'areas': areas})


@login_required
def duty_area_create(request):
    school = get_school(request)
    form   = DutyAreaForm(school, request.POST or None)
    if form.is_valid():
        area        = form.save(commit=False)
        area.school = school
        area.save()
        messages.success(request, f"Duty area '{area}' created.")
        return redirect('duty_area_list')
    return render(request, 'duties/area_form.html', {'form': form, 'title': 'Add Duty Area'})


@login_required
def duty_area_update(request, pk):
    school = get_school(request)
    area   = get_object_or_404(DutyArea, pk=pk, school=school)
    form   = DutyAreaForm(school, request.POST or None, instance=area)
    if form.is_valid():
        form.save()
        messages.success(request, "Duty area updated.")
        return redirect('duty_area_list')
    return render(request, 'duties/area_form.html', {'form': form, 'title': 'Edit Duty Area'})


# ── AUTO ALLOCATE ─────────────────────────────────────────
@login_required
def allocate_view(request):
    # Allow both admins and prefects
    if request.user.role not in ['admin', 'prefect', 'superadmin']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')



# ── MANUAL ASSIGN ─────────────────────────────────────────
@login_required
def manual_assign(request):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can manually assign duties.")
        return redirect('duty_area_list')

    school = get_school(request)
    term   = Term.objects.filter(school=school, is_current=True).first()
    form   = ManualAssignForm(school, term, request.POST or None)

    if form.is_valid():
        assignment        = form.save(commit=False)
        assignment.school = school
        assignment.term   = term
        assignment.method = 'manual'
        assignment.assigned_by = request.user
        assignment.save()
        messages.success(request, "Duty manually assigned.")
        return redirect('duty_area_list')

    return render(request, 'duties/manual_assign.html', {'form': form})


# ── SWAP REQUEST ──────────────────────────────────────────
@login_required
def swap_request(request):
    school = get_school(request)
    term   = Term.objects.filter(school=school, is_current=True).first()
    form   = SwapRequestForm(school, term, request.POST or None)

    if form.is_valid():
        swap              = form.save(commit=False)
        swap.school       = school
        swap.term         = term
        swap.rotation     = int(request.POST.get('rotation', 1))
        swap.requested_by = request.user
        swap.save()
        messages.success(request, "Swap request submitted. Awaiting admin approval.")
        return redirect('swap_list')

    return render(request, 'duties/swap_form.html', {'form': form})


@login_required
def swap_list(request):
    school = get_school(request)
    swaps  = DutySwapRequest.objects.filter(school=school).order_by('-id')
    return render(request, 'duties/swap_list.html', {'swaps': swaps})


@login_required
def swap_review(request, pk):
    if not request.user.is_school_admin():
        messages.error(request, "Only admins can approve swaps.")
        return redirect('swap_list')

    swap = get_object_or_404(DutySwapRequest, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        swap.reviewed_by = request.user
        swap.reviewed_at = timezone.now()
        swap.admin_note  = request.POST.get('admin_note', '')

        if action == 'approve':
            # Execute the swap
            try:
                a1 = DutyAssignment.objects.get(
                    term=swap.term, student=swap.from_student,
                    rotation=swap.rotation
                )
                a2 = DutyAssignment.objects.get(
                    term=swap.term, student=swap.to_student,
                    rotation=swap.rotation
                )
                a1.duty_area, a2.duty_area = a2.duty_area, a1.duty_area
                a1.method = a2.method = 'swap'
                a1.save(); a2.save()
                swap.status = 'approved'
                messages.success(request, "Swap approved and executed.")
            except DutyAssignment.DoesNotExist:
                messages.error(request, "Could not find assignments to swap.")
                swap.status = 'rejected'
        else:
            swap.status = 'rejected'
            messages.warning(request, "Swap rejected.")

        swap.save()
        return redirect('swap_list')

    return render(request, 'duties/swap_review.html', {'swap': swap})