from django.contrib import admin
from .models import Student, Class, Dorm, Form, ClassHistory


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display  = ['school', 'name', 'order']
    list_filter   = ['school']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display  = ['__str__', 'school', 'form', 'stream']
    list_filter   = ['school', 'form']


@admin.register(Dorm)
class DormAdmin(admin.ModelAdmin):
    list_display  = ['name', 'school', 'capacity']
    list_filter   = ['school']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display   = ['admission_number', 'get_full_name', 'current_class', 'dorm', 'status', 'school']
    list_filter    = ['school', 'status', 'current_class__form']
    search_fields  = ['admission_number', 'first_name', 'last_name']
    list_per_page  = 50

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(ClassHistory)
class ClassHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'old_class', 'new_class', 'changed_by', 'changed_at']
    list_filter  = ['changed_at']