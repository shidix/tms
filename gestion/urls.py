from django.urls import path
from . import views, auto_views

urlpatterns = [ 
    path('home', views.index, name='index'),
    path('change-password', views.change_password, name='change-password'),

    path('workdays/list', views.workdays_list, name='workdays-list'),
    path('workdays/search', views.workdays_search, name='workdays-search'),
    path('workdays/form', views.workdays_form, name='workdays-form'),
    path('workdays/form-save', views.workdays_form_save, name='workdays-form-save'),
    path('workdays/remove', views.workdays_remove, name='workdays-remove'),
    path('workdays/client/<int:client_id>/', views.workdays_client, name='workdays-client'),
    path('workdays/search-in-date', views.workdays_search_in_date, name='workdays-search-in-date'),

    #---------------------- ADMINS -----------------------
    path('admins', views.admins_dashboard, name='admins'),
    path('admins/list', views.admins_list, name='admins-list'),
    path('admins/search', views.admins_search, name='admins-search'),
    path('admins/form', views.admins_form, name='admins-form'),
    path('admins/remove', views.admins_remove, name='admins-remove'),
    path('admins/save', views.admins_save, name='admins-save'),

    #------------------------- MANAGERS -----------------------
    path('managers', views.managers, name='managers'),
    path('managers/list', views.managers_list, name='managers-list'),
    path('managers/search', views.managers_search, name='managers-search'),
    path('managers/form', views.managers_form, name='managers-form'),
    path('managers/remove', views.managers_remove, name='managers-remove'),
    path('managers/save', views.managers_save, name='managers-save'),
    path('managers/workdays/<int:obj_id>', views.managers_workdays, name='managers-workdays'),
    path('managers/login-by-uuid/<slug:uuid>/<slug:comp_uuid>', views.managers_login_by_uuid, name='managers-login-by-uuid'),
    path('managers/send-login-url', views.managers_send_login_url, name='managers-send-login-url'),
    path('managers/view-portal-login-url', views.managers_view_portal_login_url, name='managers-view-portal-login-url'),
    path('managers/report-pdf/<slug:worker_uuid>/<str:start_date>/<str:end_date>', views.managers_report_pdf, name='managers-report-pdf'),
    path('managers/report-pdf/<slug:worker_uuid>', views.managers_report_pdf, name='managers-report-pdf'),
    path('managers/report-full-pdf/<str:start_date>/<str:end_date>', views.managers_report_full_pdf, name='managers-report-full-pdf'),



    #---------------------- EMPLOYEES -----------------------
    path('employees', views.employees, name='employees'),
    path('employees/list', views.employees_list, name='employees-list'),
    path('employees/search', views.employees_search, name='employees-search'),
    path('employees/form', views.employees_form, name='employees-form'),
    path('employees/remove', views.employees_remove, name='employees-remove'),
    path('employees/save-email', views.employees_save_email, name='employees-save-email'),
    path('employees/save-pin', views.employees_save_pin, name='employees-save-pin'),
    path('employees/export', views.employees_export, name='employees-export'),
    path('employees/show-qr', views.employees_show_qr, name='employees-show-qr'),
    path('employees/search-month', views.employees_search_month, name='employees-search-month'),
    #path('employees/import', views.employees_import, name='employees-import'),
    

    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

# In urls.py
from django.conf.urls import handler404
from django.http import HttpResponseNotFound
import logging

def custom_404(request, exception):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0]  # take the first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')
    print(f"{ip}: 404 Not Found: {request.path}")
    return HttpResponseNotFound("Not found")

handler404 = custom_404
