from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from datetime import datetime, timedelta
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator

import uuid
import os, csv
from .reports import MonthlyReportPDF

from tms.decorators import group_required
from tms.commons import get_float, get_int, get_or_none, get_param, get_session, set_session, show_exc, generate_qr, csv_export, MESSAGES, get_city_from_ip
from .models import Company, Employee, Manager, Workday
from .forms import CompanyForm, ManagerForm

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from zoneinfo import ZoneInfo
from dateutil import relativedelta


def localtime(dt, tz=None):
    if tz is None:
        tz = ZoneInfo("Atlantic/Canary")
    return dt.astimezone(tz)



def gantt_plotly_view(items):

    # Expandimos en filas de un DataFrame
    try:
        import plotly.colors as pc
        items = sorted(items, key=lambda x: x.ini_date)
        tasks = {}
        cities = {}
        for item in items:
            if item.employee not in tasks:
                tasks[item.employee] = []
            tasks[item.employee].append(item)

        list_tasks = []
        color = 0
        for key, value in tasks.items():
            periods = []
            for item in value:
                if item.ipaddress is not None and item.ipaddress != "":
                    if item.ipaddress not in cities.keys():
                        cities[item.ipaddress] = get_city_from_ip(item.ipaddress)
                    city = cities[item.ipaddress]
                else:
                    city = item.ipaddress

                if item.ipaddress_out is not None and item.ipaddress_out != "":
                    if item.ipaddress_out not in cities.keys():
                        cities[item.ipaddress_out] = get_city_from_ip(item.ipaddress_out)
                    city_out = cities[item.ipaddress_out]
                else:
                    city_out = item.ipaddress_out

                if item.finish == True:
                    periods.append((item.ini_date.isoformat(), item.end_date.isoformat(), item.pk, city, city_out))
                else:
                    try:
                        periods.append((item.ini_date.isoformat(), item.ini_date.isoformat(), item.pk, city, city_out))
                    except Exception as e:
                        print(show_exc(e))
                        pass

            if (len(periods) > 0):
                list_tasks.append({"label": key.name, "periods": periods, "color":color})
            color += 1

        # Usa una paleta de 16 colores distintos (Plotly's qualitative palette)
        colores = pc.qualitative.Plotly  
        colores += pc.qualitative.D3  
        if len(list_tasks) > 0:
            rows = []
            milestones  = []
            for task in list_tasks:  
                for i, (start, end, uuid, ipaddress, ipaddress_out) in enumerate(task["periods"]):
                    if ipaddress == None:
                        ipaddress = "Desconocida"
                    diff = pd.to_datetime(end) - pd.to_datetime(start)
                    index = task
                    if (diff.total_seconds() > 120):
                        rows.append({
                            "Empleado": task["label"],
                            "Entrada": localtime(pd.to_datetime(start)),
                            "Salida": localtime(pd.to_datetime(end)),
                            "ID": f'{task["label"]}-{i+1}',
                            "UUID": uuid,
                            "Color": colores[task["color"]],
                            "Entrada(Loc)": ipaddress,
                            "Salida(Loc)": ipaddress_out,
                        })
                    else:
                        if (diff.total_seconds() > 0):
                            mycolor = "orange"
                            symbol = "diamond"
                        else:
                            mycolor = "red"
                            symbol = "x"
                        milestones.append({
                            "Empleado": task["label"],
                            "Entrada": localtime(pd.to_datetime(start)),
                            "Salida": localtime(pd.to_datetime(end)),
                            "ID" : f'{task["label"]}-{i+1}',
                            "UUID": uuid,
                            "Color": mycolor,
                            "Symbol": symbol,
                            "Entrada(Loc)": ipaddress,
                            "Salida(Loc)": ipaddress_out,
                        })
            if (len(rows) >0):
                df = pd.DataFrame(rows)
                fig = px.timeline(df, x_start="Entrada", x_end="Salida", y="Empleado", color="Empleado", hover_name="Empleado", custom_data=["UUID"],  
                                  hover_data= {"Entrada": "|%H:%M", "Salida": "|%H:%M", "Entrada(Loc)": True, "Salida(Loc)": True, "Empleado": False, "ID": False},)
            else:
                fig = go.Figure()

            first_day = list(items)[0].ini_date
            last_day = list(items)[-1].end_date
            diff_in_seconds = abs((last_day - first_day).total_seconds())

            if diff_in_seconds > 14 * 24 * 3600:
                dtick = 12
            elif diff_in_seconds > 7 * 24 * 3600:
                dtick = 8
            elif diff_in_seconds > 3 * 24 * 3600:
                dtick = 4
            elif diff_in_seconds > 24 * 3600:
                dtick = 1
            elif diff_in_seconds > 12 * 3600:
                dtick = 0.5
            else:
                dtick = 0.25


            fig.update_yaxes(autorange="reversed")  # Estilo Gantt
            fig.update_layout(title="", height=400, xaxis_dtick=dtick*3600000)
            

            for i, milestone in enumerate(milestones):
                marker = dict(
                    symbol=milestone["Symbol"],
                    size=10,
                    color="black",
                    line=dict(width=2, color="black"),
                )
                fig.add_trace(go.Scatter(
                    customdata=[[milestone["UUID"]]],
                    
                    x=[milestone["Entrada"]],
                    y=[milestone["Empleado"]],
                    mode="markers",
                    marker=marker,
                    text=milestone["Entrada"].strftime("%H:%M"),
                    showlegend=False,
                    name=milestone["Empleado"],
                    hovertemplate=f"<b>{milestone['Empleado']}</b><br>Entrada: {milestone['Entrada'].strftime('%H:%M')}<br>Salida: {milestone['Salida'].strftime('%H:%M')}<br>Entrada(Loc):{milestone['Entrada(Loc)']}<br>Salida(Loc):{milestone['Salida(Loc)']}<extra></extra>",
                ))

            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                name='Fichajes muy cortos',
                marker=dict(symbol='diamond', size=10, color='black')
            ))

            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                name='Fichajes abiertos',
                marker=dict(symbol='x', size=10, color='black')
            ))

            chart_div = plot(fig, output_type='div', )
            return (chart_div)
        else:
            return None
    except Exception as e:
        print(show_exc(e))
        return None

@method_decorator(never_cache, name='dispatch')
class TMSLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Perform the login
        login(self.request, form.get_user())
        # Redirect to the next page
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('index')

def redraw_plotty(request):
    try:
        items = get_workdays(request)
        gantt = gantt_plotly_view(items)
        return render(request, "gantt.html", {"gantt": gantt})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

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

    if not request.user.is_superuser:
        if Manager.objects.filter(user=request.user).exists():
            kwargs["employee__comp"] = Manager.objects.get(user=request.user).comp
        elif Employee.objects.filter(user=request.user).exists():
            kwargs["employee__comp"] = Employee.objects.get(user=request.user).comp
        else:
            raise Exception("No se ha podido obtener la empresa del usuario")

    items_started_in = Workday.objects.filter(**kwargs).order_by("-ini_date")

    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"end_date__gte": i_date, "end_date__lte": e_date}
    if value != "":
        kwargs["employee__name__icontains"] = value

    if not request.user.is_superuser:
        if Manager.objects.filter(user=request.user).exists():
            kwargs["employee__comp"] = Manager.objects.get(user=request.user).comp
        elif Employee.objects.filter(user=request.user).exists():
            kwargs["employee__comp"] = Employee.objects.get(user=request.user).comp
        else:
            raise Exception("No se ha podido obtener la empresa del usuario")

    items_finished_in = Workday.objects.filter(**kwargs).order_by("-ini_date")

    # Merge the two querysets
    items = list(items_started_in) + list(items_finished_in)
    return set(items)

@login_required
def change_password(request):
    try:
        if request.method == "POST":
            user = request.user
            password = request.POST.get("new_password1")
            user.set_password(password)
            user.save()
            # Logout the user after changing the password
            logout(request)
            login(request, user)
            return render(request, "change-password-ok.html", {"exc": MESSAGES["PASSWORD_CHANGED"],"icon":"success" }, status=200)
        return render(request, "change-password.html", {})
    except Exception as e:
        print(show_exc(e))
        return HttpResponse(MESSAGES["UNEXPECTED"], status=503)

@group_required("admins", "managers")
def index(request):
    try:
        # Check if user is in admins group
        if request.user.groups.filter(name__in="admins").exists() or request.user.is_superuser:
            return redirect(reverse("admins"))
        else:
            init_session_date(request, "s_idate")
            init_session_date(request, "s_edate")
            items = get_workdays(request)
            gantt = gantt_plotly_view(items)
            list_dates = [ datetime.now().date() + timedelta(days=i) for i in range(-6, 1) ]
            listmode = False
            return render(request, "index.html", {"item_list": items, "gantt": gantt, "list_dates": list_dates, 'listmode': listmode}) 
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins",)
def workdays_list(request):
    try:
        list_dates = [ datetime.now().date() + timedelta(days=i) for i in range(-6, 1) ]
        listmode = get_param(request.POST, "listmode", "true").lower() == "true"
        return render(request, "workdays-list.html", {"item_list": get_workdays(request), "list_dates": list_dates, 'listmode': listmode})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins","managers")
def workdays_search(request):
    try:
        set_session(request, "s_name", get_param(request.GET, "s_name"))
        set_session(request, "s_idate", get_param(request.GET, "s_idate"))
        set_session(request, "s_edate", get_param(request.GET, "s_edate"))
        items = get_workdays(request)
        chart_div = gantt_plotly_view(items)
        list_dates = [ datetime.now().date() + timedelta(days=i) for i in range(-6, 1) ]


        start_date = datetime.strptime(get_session(request, "s_idate"), "%Y-%m-%d").date()
        end_date = datetime.strptime(get_session(request, "s_edate"), "%Y-%m-%d").date()
        if (start_date == end_date):
            current_date = start_date
        else:
            current_date = None
        listmode = get_param(request.GET, "listmode", "true").lower() == "true"
        return render(request, "workdays-list.html", {"item_list": items, "gantt": chart_div, "list_dates": list_dates, 'listmode': listmode, 'current_date': current_date})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins","managers")
def workdays_search_in_date(request):
    try:
        set_session(request, "s_idate", get_param(request.POST, "day"))
        set_session(request, "s_edate", get_param(request.POST, "day"))
        items = get_workdays(request)
        chart_div = gantt_plotly_view(items)
        # last 7 days in list_dates
        list_dates = [ (datetime.now().date() + timedelta(days=i)) for i in range(-6, 1) ]
        current_date = datetime.strptime(get_session(request, "s_idate"), "%Y-%m-%d").date()
        listmode = get_param(request.POST, "listmode", "true").lower() == "true"
        
        return render(request, "workdays-list.html", {"item_list": items, "gantt": chart_div, "list_dates": list_dates, 'current_date': current_date, 'listmode': listmode})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins","managers")
def workdays_form(request):
    obj = get_or_none(Workday, get_param(request.GET, "obj_id"))
    if request.user.is_superuser:
        context = {'obj': obj, 'emp_list': Employee.objects.all()}
    else:
        if request.user.manager:
            context = {'obj': obj, 'emp_list': Employee.objects.filter(comp=request.user.manager.comp)}
            
        
    return render(request, "workdays-form.html", context)

@group_required("admins","managers")
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
    obj.setIpAddress(request)
    obj.save()
    items = get_workdays(request)
    
    gantt = gantt_plotly_view(items)
    return render(request, "workdays-list.html", {"item_list":items, "gantt": gantt})

@group_required("admins", "managers")
def workdays_remove(request):
    try:
        if request.method == "GET":
            obj = get_or_none(Workday, request.GET["obj_id"]) if "obj_id" in request.GET else None
            set_session(request, "s_name", get_param(request.GET, "s_name"))
            set_session(request, "s_idate", get_param(request.GET, "s_idate"))
            set_session(request, "s_edate", get_param(request.GET, "s_edate"))
        else:
            obj = get_or_none(Workday, request.POST["obj_id"]) if "obj_id" in request.POST else None
            set_session(request, "s_name", get_param(request.POST, "s_name"))
            set_session(request, "s_idate", get_param(request.POST, "s_idate"))
            set_session(request, "s_edate", get_param(request.POST, "s_edate"))
        if obj != None:
            obj.delete()

        items = get_workdays(request)
        gantt = gantt_plotly_view(items)
        return render(request, "workdays-list.html", {"item_list": items, "gantt": gantt})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})


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

    if not request.user.is_superuser:
        if Manager.objects.filter(user=request.user).exists():
            full_query &= Q(comp=Manager.objects.get(user=request.user).comp)
        elif Employee.objects.filter(user=request.user).exists():
            full_query &= Q(comp=Employee.objects.get(user=request.user).comp)
        else:
            raise Exception("No se ha podido obtener la empresa del usuario")
    items = Employee.objects.filter(full_query).order_by("comp__name", "name")
    for item in items:
        if len(item.uuid) < 20:
            temp_uuid = str(uuid.uuid4())
            while Employee.objects.filter(uuid=temp_uuid).exists():
                temp_uuid = str(uuid.uuid4())
            item.uuid = temp_uuid
            item.save()
    return items

@group_required("admins", "managers")
def employees(request):
    try:
        init_session_date(request, "s_emp_idate")
        init_session_date(request, "s_emp_edate")
        return render(request, "employees/employees.html", {"items": get_employees(request)})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins", "managers")
def employees_list(request):
    try:
        return render(request, "employees/employees-list.html", {"items": get_employees(request)})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins", "managers")
def employees_search(request):
    try:
        set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
        set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
        set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
        return render(request, "employees/employees-list.html", {"items": get_employees(request)})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

def employees_search_month(request):
    try:
        if request.method == "POST":
            months_ago = int(get_param(request.POST, "months_ago"))
            if (months_ago >= 0):
                start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + relativedelta.relativedelta(months=-months_ago)
                end_date = start_date + relativedelta.relativedelta(months=1) - timedelta(seconds=1)
            else: # Week search
                #Get monday from this week
                weeks_ago = abs(months_ago)-1
                start_date = datetime.now() - timedelta(days=datetime.now().weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - relativedelta.relativedelta(weeks=weeks_ago)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)

            set_session(request, "s_emp_name", get_param(request.POST, "s_emp_name"))
            set_session(request, "s_emp_idate", start_date.strftime("%Y-%m-%d"))
            set_session(request, "s_emp_edate", end_date.strftime("%Y-%m-%d"))
            items = get_employees(request)
            return render(request, "employees/employees-list.html", {"items": items})
        else:
            return render(request, "workdays-client-error.html", {})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})


@group_required("admins", "managers")
def employees_form(request):
    try:
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
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

@group_required("admins", "managers")
def employees_remove(request):
    try:
        obj = get_or_none(Employee, request.GET["obj_id"]) if "obj_id" in request.GET else None
        if obj != None:
            if obj.user != None:
                obj.user.delete()
            obj.delete()
        return render(request, "employees/employees-list.html", {"items": get_employees(request)})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})
    
@group_required("admins", "managers")
def employees_save_pin(request):
    try:
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        new_pin = get_param(request.GET, "value")
        if Employee.objects.filter(pin=new_pin, comp=obj.comp).exists():
            return HttpResponse("<strong>El PIN ya existe para esta empresa.</strong>", status=500)
        obj.pin = new_pin
        obj.save()
        return HttpResponse("Guardado!")
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

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

@group_required("admins", "managers")
def employees_show_qr(request):
    try:
        uuid = request.GET.get("uuid", None)
        if uuid == None:
            return render(request, "workdays-client-error.html", {})
        obj = Employee.objects.filter(uuid=uuid).first()
        if obj != None:
            return render(request, "employees/employees-show-qr.html", {"item": obj})
        else:
            return render(request, "workdays-client-error.html", {})
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})

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


@group_required("admins", "managers")
def managers_report_pdf(request, worker_uuid, start_date=None, end_date=None):
    try:

        if start_date is None:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        range_date = [ start_date, end_date ]
        if settings.DEBUG:
            print (f"Generating report for worker {worker_uuid} from {start_date} to {end_date}")

        employee = Employee.objects.filter(uuid=worker_uuid).first()
 
        pdf_report = MonthlyReportPDF(employee, start_date, end_date)
        output = pdf_report.output_to_memory()

        response = HttpResponse(output, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_trabajador.pdf"'
        return response

    except Exception as e:
        print(show_exc(e))
        return HttpResponse(f"<strong>Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.</strong><br>{show_exc(e)}", status=503)
    
@group_required("managers")
def managers_report_full_pdf(request, start_date=None, end_date=None):
    try:
        if start_date is None:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        range_date = [ start_date, end_date ]
        if settings.DEBUG:
            print (f"Generating report for company {request.user.manager.comp.name} from {start_date} to {end_date}")

        employees = Employee.objects.filter(comp = request.user.manager.comp)

        pdf_report = MonthlyReportPDF(employees, start_date, end_date)
        output = pdf_report.output_to_memory()

        response = HttpResponse(output, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_trabajador.pdf"'
        return response

    except Exception as e:
        print(show_exc(e))
        return HttpResponse("<strong>Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.</strong>", status=503)



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
    companies = Company.objects.all()
    new = False
    if obj == None:
        obj = Manager.objects.create()
        obj.save_user()
        obj.save()
        new = True
    return render(request, "managers/managers-form.html", {'obj': obj, 'new': new, 'companies': companies})

@group_required("admins",)
def managers_remove(request):
    obj = get_or_none(Manager, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "managers/managers-list.html", {"items": get_managers(request)})

@group_required("admins",)
def managers_save(request):
    try:
        if request.method == "POST":
            obj = get_or_none(Manager, request.POST["id"]) if "id" in request.POST else None
            if obj == None:
                uuid_temp = uuid.uuid4()
                while Manager.objects.filter(uuid=uuid_temp).exists():
                    uuid_temp = uuid.uuid4()
                obj = Manager.objects.create(uuid=str(uuid_temp))
                
            form = ManagerForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                obj = form.save(commit=False)
                if (len(obj.uuid) < 20):
                    temp_uuid = uuid.uuid4()
                    while Manager.objects.filter(uuid=temp_uuid).exists():
                        temp_uuid = uuid.uuid4()
                    obj.uuid = str(temp_uuid)
                obj.save()
                obj.save_user()
                return render(request, "managers/manager-card.html", {"item": obj})
            else:
                companies = Company.objects.all()
                return render(request, "managers/managers-form.html", {'form': form, 'obj': obj, 'new': False, 'companies':companies}, status=500)
        else:
            return redirect("managers")
    except Exception as e:
        print(show_exc(e))
        return render(request, "simple-error-alert.html", {"exc":"Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.", "modal": "common-modal"}, status=503)

@group_required("admins",)
def managers_workdays(request, obj_id):
    return render(request, "managers/managers-workdays.html", {"obj": get_or_none(Manager, obj_id)})

@group_required("admins", "managers")
def managers_send_login_url(request):
    try:
        uuid = request.GET.get("uuid", None)
        manager = Manager.objects.filter(uuid=uuid).first()
        if manager != None:
            abs_url = request.build_absolute_uri(reverse('managers-login-by-uuid', kwargs={'uuid': manager.uuid, 'comp_uuid': manager.comp.uuid}))
            return HttpResponse(abs_url, status=200)
        else:
            return HttpResponse("<small><strong>Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.</strong></small>", status=503)
    except Exception as e:
        print(show_exc(e))
        if request.user.is_superuser:
            return HttpResponse(f"<small><strong>{show_exc(e)}</strong></small>", status=503)
    return HttpResponse("<small><strong>Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.</strong></small>", status=503)

def managers_view_portal_login_url(request):
    try:
        uuid = request.GET.get("uuid", None)
        company = Company.objects.filter(uuid=uuid).first()
        if company != None:
            abs_url = request.build_absolute_uri(reverse('pwa-portal-company-login', kwargs={'uuid': company.uuid}))
            return HttpResponse(abs_url, status=200)
        else:
            return HttpResponse("<small><strong>Ha ocurrido un error inesperado. Consulte con el administrador de la plataforma.</strong></small>", status=503)
    except Exception as e:
        print(show_exc(e))
        if request.user.is_superuser:
            return HttpResponse(f"<small><strong>{show_exc(e)}</strong></small>", status=503)
    return HttpResponse("<small><strong>Ha ocurrido un error grave inesperado. Consulte con el administrador de la plataforma.</strong></small>", status=503)


def managers_login_by_uuid(request, uuid, comp_uuid):
    try:
        obj = Manager.objects.filter(uuid=uuid, comp__uuid = comp_uuid).first()
        if obj != None:
            if request.user.is_authenticated:
                logout(request)
                request.session.flush()
            request.session["company"] = obj.pk
            login(request, obj.user)
            request.session["user"] = obj.user.pk
            request.session["user_type"] = "managers"
            return redirect(reverse("index"))
        else:
            return redirect(reverse("index"))
    except Exception as e:
        print(show_exc(e))
        return redirect(reverse("index"))


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
        companies = Company.objects.all().order_by("-expiration_date", "-last_payment")
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
                return render(request, "admins/admins-row.html", {"item": obj})
            else:
                print (form.errors)
                return render(request, "admins/admins-form.html", {'form': form, 'obj': obj, 'new': False}, status=500)
        else:
            return redirect("admins")
    except Exception as e:
        print(show_exc(e))
        return render(request, "workdays-client-error.html", {})


@group_required("admins",)
def admins_remove(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "admins/admins-list.html", {"items": get_admins(request)})


'''
    TWILIO
'''
def send_welcome_sms(request):
    """
    This function is commented out because it requires Twilio configuration.
    Uncomment and configure the Twilio service to use this functionality.
    """
    return JsonResponse({"error": "This function is not implemented. Please configure Twilio to use SMS functionality."}, status=501)

# Uncomment the following lines if you want to use Twilio for sending SMS
# from .services.twilio_service import send_sms

# def send_welcome_sms(request):
#     phone_number = request.POST.get('phone_number')  # '+51987654321'
#     message = "¡Bienvenido a nuestra plataforma! Gracias por registrarte."

#     result = send_sms(phone_number, message)

#     if result["status"] == "success":
#         return JsonResponse({"message": "SMS enviado correctamente", "sid": result["sid"]})
#     else:
#         return JsonResponse({"error": result["error"]}, status=400)

