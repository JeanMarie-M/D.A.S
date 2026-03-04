from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps


def admin_required(view_func):
    """Restrict view to school admins only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_school_admin():
            messages.error(request, "⛔ Admin access required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def prefect_or_admin(view_func):
    """Allow both prefects and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ['admin', 'prefect', 'superadmin']:
            messages.error(request, "⛔ Access denied.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper