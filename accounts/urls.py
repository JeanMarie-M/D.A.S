from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.home,            name='home'),
    path('dashboard/',              views.dashboard,       name='dashboard'),
    path('login/',                  views.login_view,      name='login'),
    path('logout/',                 views.logout_view,     name='logout'),
    path('users/',                  views.user_list,       name='user_list'),
    path('users/add/',              views.user_create,     name='user_create'),
    path('users/<int:pk>/edit/',    views.user_update,     name='user_update'),
    path('users/<int:pk>/delete/',  views.user_delete,     name='user_delete'),
    path('change-password/',        views.change_password, name='change_password'),
]