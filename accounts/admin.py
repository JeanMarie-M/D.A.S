from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'school']
    list_filter  = ['role', 'school']
    fieldsets    = UserAdmin.fieldsets + (
        ('School Info', {'fields': ('role', 'school')}),
    )