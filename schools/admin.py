from django.contrib import admin
from .models import School, Term


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'email', 'is_active', 'registered_at']
    search_fields = ['name', 'code', 'email']
    list_filter   = ['is_active']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['school', 'name', 'rotation_period', 'is_current']
    list_filter  = ['school', 'is_current']