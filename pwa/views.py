from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import datetime

from tms.decorators import group_required_pwa
from tms.commons import user_in_group, get_or_none, get_param
from gestion.models import Employee, Manager, Workday


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
    logout(request)
    return redirect(reverse('pwa-login'))

'''
    EMPLOYEES
'''
@group_required_pwa("employees")
def employee_home(request):
    workday = Workday.objects.filter(employee=request.user.employee, finish=False).first()
    return render(request, "pwa/employees/home.html", {"obj": workday})

@group_required_pwa("employees")
def employee_qr_scan(request):
    return render(request, "pwa/employees/qr-scan.html")

@group_required_pwa("employees")
def employee_qr_scan_finish(request):
    return render(request, "pwa/employees/qr-scan-finish.html")

@group_required_pwa("employees")
def employee_qr_read(request):
    try:
        qr_val = request.POST["qr_value"].split("/")
        #client = get_or_none(Manager, qr_val[6])
        obj = Workday.objects.create(employee=request.user.employee, ini_date=datetime.now())
        #assistance = Assistance.objects.filter(client = client).order_by("-ini_date").first()
        #if assistance == None or assistance.finish == True:
        #    Assistance.objects.create(client=client, employee=request.user.employee)
        #else:
        #    assistance.finish = True
        #    assistance.save()
        #if client.observations != "":
        #    return render(request, "pwa/employees/client-obs.html", {"client": client})
        return redirect("pwa-home")
        #return render(request, "pwa/employees/qr-read.html", {"value": qr_val})
    except Exception as e:
        return render(request, "pwa/employees/qr-error.html", {})
        #return HttpResponse("Error: QR no válido ({})".format(e))

@group_required_pwa("employees")
#def employee_qr_finish(request, obj_id):
def employee_qr_finish(request):
    try:
        qr_val = request.POST["qr_value"].split("/")
        #client = get_or_none(Manager, qr_val[6])
        obj = Workday.objects.filter(employee=request.user.employee, finish=False).order_by("-ini_date").first()
        #obj = get_or_none(Assistance, obj_id)
        obj.end_date = datetime.now() 
        obj.finish = True
        obj.save()
        return redirect("pwa-home")
    except Exception as e:
        return render(request, "pwa/employees/qr-error.html", {})
     
@group_required_pwa("employees")
def employee_code_read(request):
    try:
        code = get_param(request.POST, "code")
        if code == "":
            return render(request, "pwa/employees/qr-error.html", {})

        #client = get_or_none(Manager, code, "code")
        #if client == None:
        #    return render(request, "pwa/employees/qr-error.html", {})

        obj = Workday.objects.create(employee=request.user.employee, ini_date=datetime.now())
        #if client.observations != "":
        #    return render(request, "pwa/employees/client-obs.html", {"client": client})
        return redirect("pwa-home")
    except Exception as e:
        print(e)
        return render(request, "pwa/employees/qr-error.html", {})

@group_required_pwa("employees")
def employee_code_finish(request):
    try:
        code = get_param(request.POST, "code")
        if code == "":
            return render(request, "pwa/employees/qr-error.html", {})

        #client = get_or_none(Manager, code, "code")
        #if client == None:
        #    return render(request, "pwa/employees/qr-error.html", {})

        obj = Workday.objects.filter(employee=request.user.employee, finish=False).order_by("-ini_date").first()
        obj.end_date = datetime.now() 
        obj.finish = True
        obj.save()
        return redirect("pwa-home")
    except Exception as e:
        return render(request, "pwa/employees/qr-error.html", {})
 
