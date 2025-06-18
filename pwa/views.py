from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import timedelta
from datetime import datetime

from tms.decorators import group_required_pwa
from tms.commons import user_in_group, get_or_none, get_param, show_exc
from gestion.models import Employee, Manager, Workday, Company
import random, json, uuid


@group_required_pwa("employees")
def index(request):
    try:
        return redirect(reverse('pwa-employee'))
    except:
        return redirect(reverse('pwa-login'))

def pin_login(request):
    CONTROL_KEY = "SZRf2QMpIfZHPEh0ib7YoDlnnDp5HtjDqbAw"
    msg = ""  
    if request.method == "POST":
        context =  {}
        msg = "Operación no permitida"
        pin = request.POST.get('pin', None)
        control_key = request.POST.get('control_key', None)
        if pin != None and control_key != None:
            if control_key == CONTROL_KEY:
                try:
                    emp = get_or_none(Employee, pin, "pin")
                    login(request, emp.user)
                    request.session['pwa_app_session'] = True
                    return redirect(reverse('pwa-employee'))
                except Exception as e:
                    msg = "Pin no válido"
                    print(e)
            else:
                msg = "Bad control"
    return render(request, "pwa-login.html", {'msg': msg})

def pin_logout(request):
    try:
        if request.user.is_authenticated:
            comp_uuid = request.user.employee.comp.uuid
            logout(request)
            return redirect(reverse('pwa-portal-company-login', kwargs={'uuid': comp_uuid}))
        else:
            return redirect(reverse('pwa-login'))
    except Exception as e:
        print(show_exc(e))
        return redirect(reverse('pwa-login'))

'''
    EMPLOYEES
'''
def get_workday_list(year, month):
    return Workday.objects.filter(ini_date__year=year, ini_date__month=month, finish=True).order_by("-ini_date")

@group_required_pwa("employees")
def employee_home(request):
    if user_in_group(request.user, "employees"):
        today = datetime.today()
        if (len(request.user.employee.uuid) < 20):
            temp_uuid = str(uuid.uuid4())
            while (Employee.objects.filter(uuid=temp_uuid, comp = request.user.employee.comp).exists()):
                temp_uuid = str(uuid.uuid4())
            request.user.employee.uuid = temp_uuid
            request.user.employee.save()
        workday = Workday.objects.filter(employee=request.user.employee, finish=False).first()
        workday_list = Workday.objects.filter(employee=request.user.employee, ini_date__year=today.year, ini_date__month=today.month, finish=True).order_by("-ini_date")
        context = {
            "obj": workday, 
            'item_list': workday_list, 
            'year_list': range(2025, 2050), 
            'current_year': today.year, 
            'month_list': range(1, 13), 
            'current_month': today.month,
            'employee': request.user.employee,
        }
        return render(request, "pwa/employees/home.html", context)
    else:
        # Check if company is set in request  
        if hasattr(request, 'uuid_company'):
            return redirect(reverse('pwa-company-login', kwargs={'uuid': request.uuid_company}))
        return render(request, "pwa/employees/qr-error.html", {})


@group_required_pwa("employees")
def employee_update_year(request):
    year = get_param(request.GET, "value")
    month = get_param(request.GET, "month")
    workday_list = get_workday_list(year, month)
    workday_list = workday_list.filter(employee = request.user.employee).order_by("-ini_date")

    return render(request, "pwa/employees/workdays-list.html", {'item_list': workday_list,})

@group_required_pwa("employees")
def employee_update_month(request):
    month = get_param(request.GET, "value")
    year = get_param(request.GET, "year")
    workday_list = get_workday_list(year, month)
    workday_list = workday_list.filter(employee = request.user.employee).order_by("-ini_date")
    return render(request, "pwa/employees/workdays-list.html", {'item_list': workday_list,})

def employee_qr_scan(request):
    return render(request, "pwa/employees/qr-scan.html")

@group_required_pwa("employees")
def employee_qr_scan_finish(request):
    return render(request, "pwa/employees/qr-scan-finish.html")

@group_required_pwa("employees")
def employee_qr_read(request):
    try:
        qr_val = request.POST["qr_value"].split("/")
        comp = get_or_none(Company, qr_val[6])
        if comp != request.user.employee.comp:
            return render(request, "pwa/employees/qr-error.html", {})
        obj = Workday.objects.create(employee=request.user.employee, ini_date=datetime.now())
        return redirect("pwa-home")
    except Exception as e:
        return render(request, "pwa/employees/qr-error.html", {})

@group_required_pwa("employees")
def employee_qr_finish(request):
    try:
        qr_val = request.POST["qr_value"].split("/")
        comp = get_or_none(Company, qr_val[6])
        if comp != request.user.employee.comp:
            return render(request, "pwa/employees/qr-error.html", {})
        obj = Workday.objects.filter(employee=request.user.employee, finish=False).order_by("-ini_date").first()
        obj.end_date = datetime.now() 
        obj.finish = True
        obj.setIpAddress(request)
        obj.save()
        return redirect("pwa-home")
    except Exception as e:
        return render(request, "pwa/employees/qr-error.html", {})
    
def employee_check_clock(request, uuid = None):
    try:
        if (uuid == None):
            if request.user.is_authenticated:
                if hasattr(request.user, 'employee'):
                    emp = request.user.employee
                    uuid = emp.uuid
                else:
                    return render(request, "pwa/employees/qr-error.html", {})
        else:
            emp = get_or_none(Employee, uuid, "uuid")
        if emp == None:
            return render(request, "pwa/employees/qr-error.html", {})
        
        obj = Workday.objects.filter(employee=emp, finish=False).order_by("-ini_date").first()
        if obj != None:
            obj.end_date = datetime.now()
            obj.finish = True
            obj.setIpAddress(request)
            obj.save()
        else:
            obj = Workday.objects.create(employee=emp, ini_date=datetime.now())
            obj.setIpAddress(request)
            obj.save()
        # Register ipaddress
        return redirect(reverse('pwa-view-clock', kwargs={'id': obj.pk, 'uuid': emp.uuid}))

        return render(request, "pwa/employees/company-sign-in.html", {'comp': emp.comp, 'obj': obj})
    except Exception as e:
        print(show_exc(e))
        return render(request, "pwa/employees/qr-error.html", {})

def employee_view_clock(request, id=None, uuid=None):
    try:
        if uuid == None:
            if request.user.is_authenticated:
                if hasattr(request.user, 'employee'):
                    emp = request.user.employee
                    uuid = emp.uuid
                else:
                    return render(request, "pwa/employees/qr-error.html", {})
            return render(request, "pwa/employees/qr-error.html", {})
        else:
            obj = Workday.objects.filter(pk=id, employee__uuid=uuid).first()
            emp = obj.employee if obj else None
            return render(request, "pwa/employees/company-sign-in.html", {'comp': emp.comp, 'obj': obj})
    except Exception as e:
        print(show_exc(e))
        return render(request, "pwa/employees/qr-error.html", {})

def pwa_company_login(request, uuid=None):
    try:
        if request.method == "POST":
            uuid = request.POST.get('uuid', None)
            if uuid == None:
                return render(request, "pwa/employees/qr-error.html", {})
            comp = get_or_none(Company, uuid, "uuid")
            pin = request.POST.get('pin', None)
            remember = request.POST.get('remember', None)

            if pin != None:
                try:
                    emp = Employee.objects.filter(comp=comp, pin=pin).get()
                    if emp == None:
                        print(1)
                        return render(request, "pwa/employees/company-login.html", {'comp': comp})
                    
                    if request.user.is_authenticated:
                        if hasattr(request.user, 'employee'):
                            if request.user.employee.comp != comp:
                                return render(request, "pwa/employees/company-login.html", {'comp': comp})
                            else:
                                if (Workday.objects.filter(employee=request.user.employee, finish=False).exists()):
                                    obj = Workday.objects.filter(employee=request.user.employee, finish=False).order_by("-ini_date").first()
                                    obj.end_date = datetime.now()
                                    obj.finish = True
                                    obj.setIpAddress(request)
                                    obj.save()
                                else:
                                    obj = Workday.objects.create(employee=request.user.employee, ini_date=datetime.now())
                                    obj.setIpAddress(request)
                                    obj.save()
                                return render(request, "pwa/employees/company-sign-in.html", {'comp': comp, 'obj': obj})

                        else:
                            if request.user.is_superuser:
                                emp = Employee.objects.filter(comp=comp, pin=pin).get()
                                if emp != None:
                                    obj = Workday.objects.filter(employee=emp, finish=False).order_by("-ini_date").first()
                                    if obj != None:
                                        obj.end_date = datetime.now()
                                        obj.finish = True
                                        obj.setIpAddress(request)
                                        obj.save()
                                    else:
                                        obj = Workday.objects.create(employee=emp, ini_date=datetime.now())
                                        obj.setIpAddress(request)
                                        obj.save()
                                return render(request, "pwa/employees/company-sign-in.html", {'comp': comp, 'obj': obj})

                    else:
                        emp = Employee.objects.filter(comp=comp, pin=pin).get()
                        if emp != None:
                            if remember != "on":
                                if (Workday.objects.filter(employee=emp, finish=False).exists()):
                                    obj = Workday.objects.filter(employee=emp, finish=False).order_by("-ini_date").first()
                                    obj.end_date = datetime.now()
                                    obj.finish = True
                                    obj.setIpAddress(request)
                                    obj.save()
                                else:
                                    obj = Workday.objects.create(employee=emp, ini_date=datetime.now())
                                    obj.setIpAddress(request)
                                    obj.save()
                                return render(request, "pwa/employees/company-sign-in.html", {'comp': comp, 'obj': obj})
                            else:
                                login(request, emp.user)
                                request.session['pwa_app_session'] = True
                                return redirect(reverse('pwa-employee'))
           
                        else:
                            return redirect(reverse('pwa-company-login', kwargs={'uuid': uuid}))

                    return render(request, "pwa/employees/company-login.html", {'comp': comp})
                except Exception as e:
                    print(show_exc(e))
                    return render(request, "pwa/employees/qr-error.html", {"comp":comp, 'msg': "Pin no válido"})
        else:
            comp = get_or_none(Company, uuid, "uuid")
            if comp == None:
                return render(request, "pwa/employees/qr-error.html", {})
            if request.user.is_superuser:
                return render(request, "pwa/employees/company-login.html", {'comp': comp})
            if request.user.is_authenticated:
                if hasattr(request.user, 'employee'):
                    if request.user.employee.comp != comp:
                        logout(request)
                        return render(request, "pwa/employees/company-login.html", {'comp': comp})
                    else:
                        return redirect(reverse('pwa-employee'))
                elif hasattr(request.user, 'manager'):
                    return render(request, "pwa/employees/company-login.html", {'comp': comp})
                else:
                    return render(request, "pwa/employees/qr-error.html", {})
            return render(request, "pwa/employees/company-login.html", {'comp': comp})
    except Exception as e:
        print(show_exc(e))
        return render(request, "pwa/employees/qr-error.html", {})
    return render(request, "pwa/employees/qr-error.html", {})

def pwa_company_private_zone(request, uuid=None):
    try:            
        if request.method == "POST":
            uuid = request.POST.get('uuid', None)
            comp = get_or_none(Company, uuid, "uuid")
            if comp == None:
                return render(request, "pwa/employees/qr-error.html", {'msg': "No se ha encontrado la empresa"})
            pin = request.POST.get('pin', None)
            if request.user.is_authenticated:
                logout(request)           
            if pin != None:
                try:
                    emp = Employee.objects.filter(comp=comp, pin=pin).get()
                    if emp == None:
                        return render(request, "pwa/employees/company-private-zone.html", {'comp': comp})
                    login(request, emp.user)
                    return redirect(reverse('pwa-employee'))
                except Exception as e:
                    print(show_exc(e))
                    return render(request, "pwa/employees/qr-error.html", {'msg': "Pin no válido"})
        else:
            if request.user.is_authenticated:
                if hasattr(request.user, 'employee'):
                    return redirect(reverse('pwa-employee'))
                else:
                    comp = get_or_none(Company, uuid, "uuid")
            else:
                comp = get_or_none(Company, uuid, "uuid")
            if comp == None:
                return render(request, "pwa/employees/qr-error.html", {'msg': "No se ha encontrado la empresa"})
            return render(request, "pwa/employees/company-private-zone.html", {'comp': comp})
    except Exception as e:
        print(show_exc(e))
        return render(request, "pwa/employees/qr-error.html", {'Ha habido un problema, por favor, inténtelo más tarde'})
    return render(request, "pwa/employees/qr-error.html", {'msg': "No se ha encontrado la empresa"})

def pwa_portal_company_login(request, uuid):
    try:
        comp = get_or_none(Company, uuid, "uuid")
        if comp == None:
            return render(request, "pwa/employees/qr-error.html", {})
        return render(request, "pwa/employees/company-login.html", {'comp': comp})
    except Exception as e:
        print(show_exc(e))
        return render(request, "pwa/employees/qr-error.html", {})
    
#@group_required_pwa("employees")
#def employee_code_read(request):
#    try:
#        code = get_param(request.POST, "code")
#        if code == "":
#            return render(request, "pwa/employees/qr-error.html", {})
#
#        #client = get_or_none(Manager, code, "code")
#        #if client == None:
#        #    return render(request, "pwa/employees/qr-error.html", {})
#
#        obj = Workday.objects.create(employee=request.user.employee, ini_date=datetime.now())
#        #if client.observations != "":
#        #    return render(request, "pwa/employees/client-obs.html", {"client": client})
#        return redirect("pwa-home")
#    except Exception as e:
#        print(e)
#        return render(request, "pwa/employees/qr-error.html", {})
#
#@group_required_pwa("employees")
#def employee_code_finish(request):
#    try:
#        code = get_param(request.POST, "code")
#        if code == "":
#            return render(request, "pwa/employees/qr-error.html", {})
#
#        #client = get_or_none(Manager, code, "code")
#        #if client == None:
#        #    return render(request, "pwa/employees/qr-error.html", {})
#
#        obj = Workday.objects.filter(employee=request.user.employee, finish=False).order_by("-ini_date").first()
#        obj.end_date = datetime.now() 
#        obj.finish = True
#        obj.save()
#        return redirect("pwa-home")
#    except Exception as e:
#        return render(request, "pwa/employees/qr-error.html", {})
# 
