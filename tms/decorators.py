from django.shortcuts import render, redirect
#from .common_lib import get_adviser, get_client
from gestion.models import Employee, Company, Manager

def group_required(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            if request.user.is_superuser:
                return f(request, *args, **kwargs)
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)):
                    if Employee.objects.filter(user=request.user).exists():
                        employee= Employee.objects.get(user=request.user)
                        if not employee.comp.is_active:
                            return render(request, "error_exception.html", {'exc':"La empresa a la que pertenece este usuario no esta activa, por favor contacte con el administrador del sistema"})
                    if Manager.objects.filter(user=request.user).exists():
                        manager = Manager.objects.get(user=request.user)
                        if not manager.comp.is_active:
                            return render(request, "no-payment.html", {'exc':"La empresa a la que pertenece este usuario no esta activa, por favor contacte con el administrador del sistema"})
                
                        
                    return f(request, *args, **kwargs)
                else:
                	return (render(request, "error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('auth_login')
        return _arguments_wrapper
    return _method_wrapper

def group_required_pwa(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)) or request.user.is_superuser:
                    return f(request, *args, **kwargs)
                else:
                	return (render(request, "error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('pwa-login')
        return _arguments_wrapper
    return _method_wrapper

