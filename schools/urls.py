from django.urls import path
from . import views
from . import wizard

urlpatterns = [
    # School
    path('register/',               views.school_register,  name='school_register'),
    path('profile/',                views.school_profile,   name='school_profile'),

    # Terms
    path('terms/',                  views.term_list,        name='term_list'),
    path('terms/add/',              views.term_create,      name='term_create'),
    path('terms/<int:pk>/edit/',    views.term_update,      name='term_update'),
    path('terms/<int:pk>/current/', views.term_set_current, name='term_set_current'),
    path('terms/<int:pk>/delete/',  views.term_delete,      name='term_delete'),

    # Setup Wizard
    path('setup/',              wizard.wizard_home,       name='wizard_home'),
    path('setup/term/',         wizard.wizard_term,       name='wizard_term'),
    path('setup/forms/',        wizard.wizard_forms,      name='wizard_forms'),
    path('setup/classes/',      wizard.wizard_classes,    name='wizard_classes'),
    path('setup/dorms/',        wizard.wizard_dorms,      name='wizard_dorms'),
    path('setup/duty-areas/',   wizard.wizard_duty_areas, name='wizard_duty_areas'),
    path('setup/students/',     wizard.wizard_students,   name='wizard_students'),
]