from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from datetime import timedelta
from datetime import datetime
from django.template.loader import render_to_string

from tms.decorators import group_required_pwa
from tms.commons import user_in_group, get_or_none, get_param, show_exc
from gestion.models import Employee, Manager, Workday, Company, WorkdayModification
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
        if request.user.is_authenticated:
            logout(request)
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

@group_required_pwa("employees")    
def pwa_request_modification(request):
    if request.method == "POST":
        try:
            workday_id = get_param(request.POST, "id")
            workday = get_or_none(Workday, workday_id)
            if workday == None:
                return JsonResponse({'error': 'Solicitud no completada.'}, status=404)
            
            modifications = workday.modifications.all().order_by('-mod_date')
            if modifications.exists():
                mod = modifications.first()
                if mod.status == 0:
                    if (mod.requested_by == request.user):
                        return JsonResponse({'title': 'Existe una solicitud pendiente para este registro. Esperando la evaluación de la empresa.', 'deny-url': reverse('pwa-modifications-history', args=[workday.id])}, status=400)
                    else:
                        url_confirm = reverse('pwa-modification-approve', args=[mod.id])
                        url_reject = reverse('pwa-modification-reject', args=[mod.id])
                        deny_text = "Rechazar"
                        confirm_text = "Aprobar"
                        html_content = render_to_string("pwa/employees/employee-modifications-pending.html", context={"workday": workday, "modification": mod}, request=request)
                        return JsonResponse({'title': 'La empresa ha solicitado una modificación.', 'html': html_content, 'deny-url':
                                              url_reject, 'confirm-url': url_confirm, 'deny-text': deny_text, 'confirm-text': confirm_text}, status=400)
            return JsonResponse({'html': render_to_string("pwa/employees/request-modification-form.html", context={"workday": workday}, request=request), 'deny-url': reverse('pwa-modifications-history', args=[workday.id])}, status=200)

        except Exception as e:
            print(show_exc(e))
            return JsonResponse({'error': 'Ha habido un error al procesar la solicitud.'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@group_required_pwa("employees")
def pwa_submit_modification(request):
    if request.method == "POST":
        try:
            workday_id = get_param(request.POST, "workday_id")
            reason = get_param(request.POST, "reason")
            new_ini_date_str = get_param(request.POST, "ini_date")
            new_end_date_str = get_param(request.POST, "end_date")

            workday = get_or_none(Workday, workday_id)
            if workday == None:
                return JsonResponse({'error': 'Solicitud no completada. Workday no encontrado.'}, status=404)

            new_ini_date = datetime.strptime(new_ini_date_str, "%Y-%m-%dT%H:%M")
            new_end_date = datetime.strptime(new_end_date_str, "%Y-%m-%dT%H:%M")

            modification_request = WorkdayModification.objects.create(
                workday=workday,
                requested_by=request.user,
                reason=reason,
                ini_date=new_ini_date,
                end_date=new_end_date
            )
            modification_request.save()

            html_content = render_to_string("pwa/employees/workdays-list-item.html", context={"item": workday}, request=request)

            return JsonResponse({'message': 'Solicitud de modificación enviada con éxito.', 'updated_html': html_content}, status=200)
        except Exception as e:
            print(show_exc(e))
            return JsonResponse({'error': 'Ha habido un error al enviar la solicitud. Por favor, inténtelo de nuevo.'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@group_required_pwa("employees")
def employee_modifications_pending(request, workday_id): 
    try:
        workdays = Workday.objects.filter(employee=request.user.employee, modifications__status=0).distinct().order_by('-ini_date')
        return JsonResponse({'html': render_to_string("pwa/employees/employee-modifications-pending.html", context={"workdays": workdays}, request=request)}, status=200)
    except Exception as e:
        print(show_exc(e))
        return JsonResponse({'error': 'Ha habido un error al obtener las modificaciones pendientes.'}, status=500)

@group_required_pwa("employees")
def employee_modifications_history(request, workday_id):
    try:
        workday = get_or_none(Workday, workday_id)
        if workday == None:
            return JsonResponse({'error': 'Registro no encontrado.'}, status=404)
        return JsonResponse({'html': render_to_string("pwa/employees/employee-modifications-history.html", context={"workday": workday}, request=request), 'width': '95%'}, status=200)
    except Exception as e:
        print(show_exc(e))
        return JsonResponse({'error': 'Ha habido un error al obtener el historial de modificaciones.'}, status=500)
    
@group_required_pwa("employees")
def employee_modification_approve(request, mod_id):
    try:
        modification = get_or_none(WorkdayModification, mod_id)
        if modification == None:
            return JsonResponse({'error': 'Modificación no encontrada.'}, status=404)
        if modification.status != 0:
            return JsonResponse({'error': 'La modificación ya ha sido procesada.'}, status=400)
        if not modification.can_user_response(request.user):
            return JsonResponse({'error': 'No tiene permiso para aprobar esta modificación.'}, status=403)
        
        modification.accepted_by = request.user
        modification.status = 1
        modification.save()
        html_content = render_to_string("pwa/employees/employee-modifications-history.html", context={"workday": modification.workday}, request=request)
        html_updated = render_to_string("pwa/employees/workdays-list-item.html", context={"item": modification.workday, "request": request}, request=request)
        return JsonResponse({'message': 'Modificación aprobada con éxito.', 'html': html_content, 'updated_html': html_updated}, status=200)
    except Exception as e:
        print(show_exc(e))
        return JsonResponse({'error': 'Ha habido un error al aprobar la modificación.'}, status=500)
    
@group_required_pwa("employees")
def employee_modification_reject(request, mod_id):
    try:
        modification = get_or_none(WorkdayModification, mod_id)
        if modification == None:
            return JsonResponse({'error': 'Modificación no encontrada.'}, status=404)
        if modification.status != 0:
            return JsonResponse({'error': 'La modificación ya ha sido procesada.'}, status=400)
        if not modification.can_user_response(request.user):
            return JsonResponse({'error': 'No tiene permiso para rechazar esta modificación.'}, status=403)
        
        modification.accepted_by = request.user
        modification.status = 2
        modification.save()
        html_content = render_to_string("pwa/employees/employee-modifications-history.html", context={"workday": modification.workday}, request=request)
        html_updated = render_to_string("pwa/employees/workdays-list-item.html", context={"item": modification.workday, "request": request}, request=request)
        return JsonResponse({'message': 'Modificación rechazada con éxito.', 'html': html_content, 'updated_html': html_updated}, status=200)
    except Exception as e:
        print(show_exc(e))
        return JsonResponse({'error': 'Ha habido un error al rechazar la modificación.'}, status=500)

    
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
