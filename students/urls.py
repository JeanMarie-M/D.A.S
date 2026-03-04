from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.student_list,           name='student_list'),
    path('add/',                views.student_create,         name='student_create'),
    path('<int:pk>/edit/',      views.student_update,         name='student_update'),
    path('<int:pk>/delete/',    views.student_delete,         name='student_delete'),
    path('<int:pk>/',           views.student_detail,         name='student_detail'),
    path('import/',             views.student_import,         name='student_import'),
    path('import/template/',    views.download_import_template, name='import_template'),
    path('bulk-delete/',        views.student_bulk_delete,    name='student_bulk_delete'),
]