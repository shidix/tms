from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
import uuid
import os, csv

from tms.decorators import group_required
from tms.commons import get_float, get_int, get_or_none, get_param, get_session, set_session, show_exc, generate_qr, csv_export
from .models import Company, Employee, Manager, Workday
from .forms import CompanyForm


def init_session_date(request, key):
    #if not key in request.session:
    set_session(request, key, datetime.now().strftime("%Y-%m-%d"))

def get_workdays(request):
    value = get_session(request, "s_name")
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"ini_date__gte": i_date, "ini_date__lte": e_date}
    if value != "":
        kwargs["employee__name__icontains"] = value

    return Workday.objects.filter(**kwargs).order_by("-ini_date")

@group_required("admins", "managers")
def index(request):
    init_session_date(request, "s_idate")
    init_session_date(request, "s_edate")
    return render(request, "index.html", {"item_list": get_workdays(request)})

@group_required("admins",)
def workdays_list(request):
    return render(request, "workdays-list.html", {"item_list": get_workdays(request)})

@group_required("admins",)
def workdays_search(request):
    set_session(request, "s_name", get_param(request.GET, "s_name"))
    set_session(request, "s_idate", get_param(request.GET, "s_idate"))
    set_session(request, "s_edate", get_param(request.GET, "s_edate"))
    return render(request, "workdays-list.html", {"item_list": get_workdays(request)})

@group_required("admins",)
def workdays_form(request):
    obj = get_or_none(Workday, get_param(request.GET, "obj_id"))
    context = {'obj': obj, 'emp_list': Employee.objects.all()}
    return render(request, "workdays-form.html", context)

@group_required("admins",)
def workdays_form_save(request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    obj = get_or_none(Workday, get_param(request.GET, "obj_id"))
    if obj == None:
        obj = Workday.objects.create()
    obj.employee = get_or_none(Employee, get_param(request.GET, "employee"))
    ini_date = get_param(request.GET, "ini_date")
    end_date = get_param(request.GET, "end_date")
    ini_time = get_param(request.GET, "ini_time")
    end_time = get_param(request.GET, "end_time")
    finish = get_param(request.GET, "finish")
    idate = datetime.strptime("{} {}".format(ini_date, ini_time), "%Y-%m-%d %H:%M")
    edate = datetime.strptime("{} {}".format(end_date, end_time), "%Y-%m-%d %H:%M")
    idate = idate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    edate = edate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    idate = idate.astimezone(ZoneInfo("UTC"))
    edate = edate.astimezone(ZoneInfo("UTC"))

    obj.ini_date = idate
    obj.end_date = edate
    obj.finish = True if finish != "" else False
    obj.save()
    return render(request, "workdays-list.html", {"item_list": get_workdays(request)})

@group_required("admins",)
def workdays_remove(request):
    obj = get_or_none(Workday, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "workdays-list.html", {"item_list": get_workdays(request)})

def workdays_client(request, client_id):
    return render(request, "workdays-client-error.html", {})

'''
    EMPLOYEES
'''
def get_employees(request):
    search_value = get_session(request, "s_emp_name")
    filters_to_search = ["name__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Employee.objects.filter(full_query)

@group_required("admins", "managers")
def employees(request):
    init_session_date(request, "s_emp_idate")
    init_session_date(request, "s_emp_edate")
    return render(request, "employees/employees.html", {"items": get_employees(request)})

@group_required("admins", "managers")
def employees_list(request):
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins", "managers")
def employees_search(request):
    set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
    set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
    set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins", "managers")
def employees_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Employee, obj_id)
    if obj == None:
        try:
            obj = Employee.objects.create(comp=request.user.manager.comp)
        except:
            obj = Employee.objects.create()
    # Check if request.user is a admin or manager
    if request.user.is_superuser:
        companies = Company.objects.all()
    else:
        companies = Company.objects.filter(pk = request.user.manager.comp.pk)

    return render(request, "employees/employees-form.html", {'obj': obj, 'companies': companies})

@group_required("admins", "managers")
def employees_remove(request):
    obj = get_or_none(Employee, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        if obj.user != None:
            obj.user.delete()
        obj.delete()
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("admins", "managers")
def employees_save_email(request):
    try:
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        obj.email = get_param(request.GET, "value")
        obj.save()
        obj.save_user()
        return HttpResponse("Saved!")
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("admins", "managers")
def employees_export(request):
    header = ['Nombre', 'Teléfono', 'Email', 'PIN', 'DNI', 'Horas trabajadas', 'Minutos trabajados']
    values = []
    items = get_employees(request)
    for item in items:
        hours, minutes = item.worked_time(request.session["s_emp_idate"], request.session["s_emp_edate"])
        row = [item.name, item.phone, item.email, item.pin, item.dni, hours, minutes]
        values.append(row)
    return csv_export(header, values, "empleados")

#@group_required("Administradores",)
#def employees_import(request):
#    f = request.FILES["file"]
#    lines = f.read().decode('latin-1').splitlines()
#    i = 0
#    for line in lines:
#        if i > 0:
#            l = line.split(";")
#            #print(l)
#            name = "{} {}".format(l[1], l[0])
#            phone = l[2]
#            email = l[7]
#            dni = l[6]
#            obj, created = Employee.objects.get_or_create(pin=dni, dni=dni, name=name, phone=phone, email=email)
#            obj.save_user()
#        i += 1
#    return redirect("employees")

'''
    MANAGERS
'''
def get_managers(request):
    search_value = get_session(request, "s_cli_name")
    filters_to_search = ["name__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Manager.objects.filter(full_query).order_by("-id")[:50]

@group_required("admins",)
def managers(request):
    return render(request, "managers/managers.html", {"items": get_managers(request)})

@group_required("admins",)
def managers_list(request):
    return render(request, "managers/managers-list.html", {"items": get_managers(request)})

@group_required("admins",)
def managers_search(request):
    set_session(request, "s_cli_name", get_param(request.GET, "s_cli_name"))
    return render(request, "managers/managers-list.html", {"items": get_managers(request)})

@group_required("admins",)
def managers_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Manager, obj_id)
    new = False
    if obj == None:
        obj = Manager.objects.create()
        new = True
    return render(request, "managers/managers-form.html", {'obj': obj, 'new': new})

@group_required("admins",)
def managers_remove(request):
    obj = get_or_none(Manager, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "managers/managers-list.html", {"items": get_managers(request)})

@group_required("admins",)
def managers_workdays(request, obj_id):
    return render(request, "managers/managers-workdays.html", {"obj": get_or_none(Manager, obj_id)})




'''
    ADMINS
'''
@group_required("admins",)
def get_admins(request):
    search_value = [get_session(request, "s_adm_name"), get_session(request, "s_adm_nif")]
    filters_to_search = ["name__icontains", "nif__iexact"]

    full_query = Q()
    if any(value != "" for value in search_value):
        for myfilter, value in zip(filters_to_search, search_value):
            if value != "":
                full_query |= Q(**{myfilter: value})

    return Company.objects.filter(full_query).order_by("-id")[:50]


@group_required("admins",)
def admins_dashboard(request):
    try:
        companies = Company.objects.all()
        return render(request, "admins/admins.html", {"items": companies})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})
    
@group_required("admins",)
def admins_search(request):
    set_session(request, "s_adm_name", get_param(request.GET, "s_adm_name"))
    set_session(request, "s_adm_nif", get_param(request.GET, "s_adm_nif"))
    return render(request, "admins/admins-list.html", {"items": get_admins(request)})

@group_required("admins",)
def admins_list(request):
    return render(request, "admins/admins-list.html", {"items": get_admins(request)})

@group_required("admins",)
def admins_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Company, obj_id)
    new = False
    if obj == None:
        new = True
    return render(request, "admins/admins-form.html", {'obj': obj, 'new': new})

@group_required("admins",)
def admins_save(request):
    try:
        if request.method == "POST":
            obj = get_or_none(Company, request.POST["id"]) if "id" in request.POST else None
            if obj == None:
                obj = Company.objects.create()
                
            form = CompanyForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                obj = form.save(commit=False)
                if (len(obj.uuid) < 20):
                    temp_uuid = uuid.uuid4()
                    while Company.objects.filter(uuid=temp_uuid).exists():
                        temp_uuid = uuid.uuid4()
                    obj.uuid = str(temp_uuid)
                obj.save()
                return redirect("admins")
            else:
                return render(request, "admins/admins-form.html", {'form': form, 'obj': obj, 'new': False})
        else:
            return redirect("admins")
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})
            # Use the CompanyForm to validate and save the data



@group_required("admins",)
def admins_remove(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "admins/admins-list.html", {"items": get_admins(request)})


