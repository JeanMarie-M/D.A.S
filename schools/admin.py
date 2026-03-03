from django.contrib import admin
from .models import School, Term

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    search_fields = ['name', 'code']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['school', 'name', 'rotation_period', 'is_current']
    list_filter  = ['school', 'is_current']
