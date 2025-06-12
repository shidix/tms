from django.urls import path
from pwa import views


urlpatterns = [
    path('', views.index, name="pwa-home"),
    path('home/', views.index, name="pwa-home"),
    path('login/', views.pin_login, name="pwa-login"),
    path('logoff/', views.pin_logout, name="pwa-logout"),

    path('company-login/<slug:uuid>', views.pwa_company_login, name="pwa-company-login"),
    path('company-portal-login/<slug:uuid>', views.pwa_portal_company_login, name="pwa-portal-company-login"),
    path('company-private-zone/<slug:uuid>', views.pwa_company_private_zone, name="pwa-company-private-zone"),

    path('company-login/', views.pwa_company_login, name="pwa-company-login"),
    path('company-private-zone/', views.pwa_company_private_zone, name="pwa-company-private-zone"),


    # EMPLOYEES
    path('employee/', views.employee_home, name="pwa-employee"),
    path('employee/qr-scan', views.employee_qr_scan, name="pwa-qr-scan"),
    path('employee/qr-scan-finish', views.employee_qr_scan_finish, name="pwa-qr-scan-finish"),
    path('employee/qr-read', views.employee_qr_read, name="pwa-qr-read"),
    path('employee/qr-finish', views.employee_qr_finish, name="pwa-qr-finish"),
    path('employee/update-year', views.employee_update_year, name="pwa-update-year"),
    path('employee/update-month', views.employee_update_month, name="pwa-update-month"),
    path('employee/check-clock/<slug:uuid>', views.employee_check_clock, name="pwa-check-clock"),
    path('employee/check-clock/<str:uuid>', views.employee_check_clock, name="pwa-check-clock"),

    path('employee/check-clock', views.employee_check_clock, name="pwa-check-clock"),
    path('employee/view-clock/<int:id>/<slug:uuid>', views.employee_view_clock, name="pwa-view-clock"),

    #path('employee/code-read', views.employee_code_read, name="pwa-code-read"),
    #path('employee/code-finish', views.employee_code_finish, name="pwa-code-finish"),
    #path('employee/qr-finish/<int:obj_id>', views.employee_qr_finish, name="pwa-qr-finish"),

]

