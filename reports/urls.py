from django.urls import path
from . import views

urlpatterns = [
    path('full-school/', views.report_full_school, name='report_full_school'),
    path('by-class/',    views.report_by_class,    name='report_by_class'),
    path('by-dorm/',     views.report_by_dorm,     name='report_by_dorm'),
    path('by-area/',     views.report_by_area,      name='report_by_area'),
]