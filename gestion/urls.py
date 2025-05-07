from django.urls import path
from . import views, auto_views

urlpatterns = [ 
    path('home', views.index, name='index'),
    path('workdays/list', views.workdays_list, name='workdays-list'),
    path('workdays/search', views.workdays_search, name='workdays-search'),
    path('workdays/form', views.workdays_form, name='workdays-form'),
    path('workdays/form-save', views.workdays_form_save, name='workdays-form-save'),
    path('workdays/remove', views.workdays_remove, name='workdays-remove'),
    path('workdays/client/<int:client_id>/', views.workdays_client, name='workdays-client'),

    #------------------------- MANAGERS -----------------------
    path('managers', views.managers, name='managers'),
    path('managers/list', views.managers_list, name='managers-list'),
    path('managers/search', views.managers_search, name='managers-search'),
    path('managers/form', views.managers_form, name='managers-form'),
    path('managers/remove', views.managers_remove, name='managers-remove'),
    path('managers/workdays/<int:obj_id>', views.managers_workdays, name='managers-workdays'),

    #---------------------- EMPLOYEES -----------------------
    path('employees', views.employees, name='employees'),
    path('employees/list', views.employees_list, name='employees-list'),
    path('employees/search', views.employees_search, name='employees-search'),
    path('employees/form', views.employees_form, name='employees-form'),
    path('employees/remove', views.employees_remove, name='employees-remove'),
    path('employees/save-email', views.employees_save_email, name='employees-save-email'),
    path('employees/export', views.employees_export, name='employees-export'),
    #path('employees/import', views.employees_import, name='employees-import'),

    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

