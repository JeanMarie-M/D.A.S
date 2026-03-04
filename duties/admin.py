from django.contrib import admin
from .models import DutyArea, DutyAssignment, DutySwapRequest, DutyHistory


@admin.register(DutyArea)
class DutyAreaAdmin(admin.ModelAdmin):
    list_display  = ['label', 'name', 'school', 'specialization', 'students_required', 'is_active']
    list_filter   = ['school', 'specialization', 'is_active']
    search_fields = ['name', 'label']


@admin.register(DutyAssignment)
class DutyAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'duty_area', 'rotation', 'term', 'method', 'assigned_by']
    list_filter  = ['school', 'term', 'method', 'rotation']


@admin.register(DutySwapRequest)
class SwapAdmin(admin.ModelAdmin):
    list_display = ['from_student', 'to_student', 'status', 'requested_by', 'reviewed_by']
    list_filter  = ['status', 'school']


@admin.register(DutyHistory)
class DutyHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'duty_area', 'term', 'rotation']
    list_filter  = ['school', 'term']