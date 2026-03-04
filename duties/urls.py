from django.urls import path
from . import views

urlpatterns = [
    path('areas/',              views.duty_area_list,   name='duty_area_list'),
    path('areas/add/',          views.duty_area_create, name='duty_area_create'),
    path('areas/<int:pk>/edit/', views.duty_area_update, name='duty_area_update'),
    path('allocate/',           views.allocate_view,    name='allocate'),
    path('manual-assign/',      views.manual_assign,    name='manual_assign'),
    path('swaps/',              views.swap_list,         name='swap_list'),
    path('swaps/request/',      views.swap_request,      name='swap_request'),
    path('swaps/<int:pk>/review/', views.swap_review,   name='swap_review'),
]