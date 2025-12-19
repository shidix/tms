from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext_lazy as _ 
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse

import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
import base64
from PIL import Image
from django.shortcuts import render
import uuid
from tms.commons import show_exc, MESSAGES
from django.template.loader import render_to_string



import datetime


'''
    COMPANIES
'''
def upload_logo(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "companies/logos/"
    return '/'.join([folder, datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def upload_qr(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "companies/qr/"
    return '/'.join([folder, datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def generate_qr_image(url, bg_image=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    if bg_image:
        logo = Image.open(bg_image)
        scale = 0.5**0.5 # Scale down the logo
        logo_size = (int(logo.size[0] * scale), int(logo.size[1] * scale))
        logo_size = (min(logo_size[0], img.size[0]//3), min(logo_size[1], img.size[1]//3))
        logo.thumbnail(logo_size)
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img.paste(logo, pos)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    img_data = "data:image/png;base64,{}".format(img_str)
    return img_data

def localtime(dt, tz=None):
    if tz is None:
        tz = ZoneInfo("Atlantic/Canary")
    return dt.astimezone(tz)

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name = _('Nombre'))
    logo = models.ImageField(upload_to=upload_logo, blank=True, verbose_name="Logo", help_text="Select file to upload")
    qr = models.ImageField(upload_to=upload_qr, blank=True, verbose_name="QR", help_text="Select file to upload")
    nif = models.CharField(max_length=20, verbose_name = _('NIF'), default="")
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")
    last_payment = models.DateField(verbose_name=_('Fecha último pago'), default=datetime.date.today)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Último pago'), default=0.00)
    expiration_date = models.DateField(verbose_name=_('Fecha de expiración'), default=datetime.date(2001, 1, 1))
    ccc = models.CharField(max_length=40, verbose_name=_('Código Cuenta Cotización'), default="")
    address = models.CharField(max_length=255, verbose_name=_('Dirección'), default="")
    clock_pwa_enabled = models.BooleanField(default=True, verbose_name=_('Fichaje desde PWA Habilitado'));

    def __str__(self):
        return self.name
    
    @property
    def is_active(self):
        try:
            if self.expiration_date:
                return self.expiration_date >= datetime.date.today()
        except Exception as e:
            print(show_exc(e))
            return False
        return False
    
    @property
    def employees(self):
        return Employee.objects.filter(comp=self)
    
    @property
    def view_logo(self):
        try:
            if self.logo:
                return format_html('<img src="{}" class="w-75 text-center mx-auto company-logo"/>', self.logo.url)
            return format_html('<img src="{}" class="w-25 text-center mx-auto company-logo"/>', '/static/images/logo-fichaje.png')
        except Exception as e:
            print(show_exc(e))
            return "-"

    @property
    def get_qr_login(self):
        data = reverse ('pwa-company-login', kwargs={'uuid': self.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        img_data = generate_qr_image(data, self.logo.path)
        return img_data
    
    @property
    def get_qr_private_zone(self):
        data = reverse ('pwa-company-private-zone', kwargs={'uuid': self.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        img_data = generate_qr_image(data, self.logo.path)
        return img_data

    class Meta:
        verbose_name = _('Empresa')
        verbose_name_plural = _('Empresas')


'''
    MANAGER
'''
class Manager(models.Model):
    pin = models.CharField(max_length=20, verbose_name = _('PIN'), default="")
    dni = models.CharField(max_length=20, verbose_name = _('DNI'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Razón Social'), default="")
    phone = models.CharField(max_length=20, verbose_name = _('Teléfono de contacto'), null=True, default = '0000000000')
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    user = models.OneToOneField(User, verbose_name='Usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='manager')
    comp = models.ForeignKey(Company, verbose_name=_("Empresa"), on_delete=models.SET_NULL, blank=True, null=True, related_name="managers")
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")

    def __str__(self):
        return self.name

    def portal_url(self):
        data = reverse ('pwa-portal-company-login', kwargs={'uuid': self.comp.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        return data
    
    def send_welcome_email(self):
        try:
            from django.core.mail import send_mail
            template_text = 'managers/manager_welcome_txt.html'
            template_html = 'managers/manager_welcome.html'
            logo_url = f"{settings.MAIN_URL}/static/images/logo-fichaje.png"
            context = {'manager': self, 'logo_url': logo_url}
            subject = _('Bienvenido a la plataforma de gestión de asistencias Fichamaster')
            message = render_to_string(template_text, context)
            html_message = render_to_string(template_html, context)
            from_email = settings.EMAIL_FROM_DEFAULT
            recipient_list = [self.email]
            send_mail(subject, message, from_email, recipient_list, html_message=html_message)
        except Exception as e:
            raise e
            # print(show_exc(e))

    def save_user(self):
        try:
            if self.user == None:
                if User.objects.filter(email=self.email).exists():
                    self.user = User.objects.get(email=self.email)
                else:
                    self.user = User.objects.create_user(username=self.email, email=self.email)
                self.save()
                if not Group.objects.filter(name='managers').exists():
                    group = Group.objects.create(name='managers')
                else:
                    group = Group.objects.get(name='managers') 
                
                group.user_set.add(self.user)
            else:
                if not self.user.groups.filter(name='managers').exists():
                    print("Adding user to group")
                    group = Group.objects.get(name='managers') 
                    group.user_set.add(self.user)
                self.user.save()
        except Exception as e:
            print (show_exc(e))


    class Meta:
        verbose_name = _('Administrador')
        verbose_name_plural = _('Administradores')


'''
    EMPLOYEE
'''
class Employee(models.Model):
    pin = models.CharField(max_length=20, verbose_name = _('PIN'), default="")
    dni = models.CharField(max_length=20, verbose_name = _('DNI'), default="")
    name = models.CharField(max_length=200, verbose_name = _('Nombre completo'), default="")
    phone = models.CharField(max_length=20, verbose_name = _('Teléfono de contacto'), null=True, default = '0000000000')
    weekly_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas por semana'), default=40.00)
    weekly_days = models.IntegerField(verbose_name=_('Días por semana'), default=5, help_text=_('Número de días a la semana que trabaja el empleado'))
    affiliation_number = models.CharField(max_length=20, verbose_name=_('Número de afiliación'), default="")
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    user = models.OneToOneField(User, verbose_name='Usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='employee')
    comp = models.ForeignKey(Company, verbose_name=_("Empresa"), on_delete=models.SET_NULL, blank=True, null=True)
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")
    mon_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Lunes'), default=7.5)
    tue_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Martes'), default=7.5)
    wed_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Miércoles'), default=7.5)
    thu_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Jueves'), default=7.5)
    fri_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Viernes'), default=7.5)
    sat_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Sábado'), default=0.0)
    sun_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas Domingo'), default=0.0)

    def __str__(self):
        return self.name
    
    @property
    def get_private_zone(self):
        data = reverse ('pwa-company-private-zone', kwargs={'uuid': self.comp.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        return data

    def send_welcome_email(self):
        try:
            from django.core.mail import send_mail
            template_text = 'employees/employee_welcome_txt.html'
            template_html = 'employees/employee_welcome.html'
            logo_url = f"{settings.MAIN_URL}/static/images/logo-fichaje.png"
            context = {'employee': self, 'logo_url': logo_url}
            subject = _('Bienvenido a la plataforma de gestión de asistencias Fichamaster')
            message = render_to_string(template_text, context)
            html_message = render_to_string(template_html, context)
            from_email = settings.EMAIL_FROM_DEFAULT

            recipient_list = [self.email]
            send_mail(subject, message, from_email, recipient_list, html_message=html_message)
        except Exception as e:
            raise e
            # print(show_exc(e))

    def save(self, *args, **kwargs):
        self.weekly_hours = float(self.mon_hours) + float(self.tue_hours) + float(self.wed_hours) + float(self.thu_hours) + float(self.fri_hours) + float(self.sat_hours) + float(self.sun_hours)
        total_days = 0
        if float(self.mon_hours) > 0:
            total_days += 1
        if float(self.tue_hours) > 0:
            total_days += 1
        if float(self.wed_hours) > 0:
            total_days += 1
        if float(self.thu_hours) > 0:
            total_days += 1
        if float(self.fri_hours) > 0:   
            total_days += 1
        if float(self.sat_hours) > 0:
            total_days += 1
        if float(self.sun_hours) > 0:
            total_days += 1
        self.weekly_days = total_days

        super().save(*args, **kwargs)

    def save_user(self):
        if self.user == None:
            self.user = User.objects.create_user(username=self.email, email=self.email)
            self.save()
            group = Group.objects.get(name='employees') 
            group.user_set.add(self.user)
        else:
            self.user.username = self.email
            self.user.save()

    def worked_time(self, ini_date, end_date):
        idate = "{} 00:00".format(ini_date)
        edate = "{} 23:59".format(end_date)
        item_list = self.workdays.filter(ini_date__gte=idate, end_date__lte=edate)
        hours = 0
        minutes = 0
        for item in item_list:
            if item.finish:
                diff = item.end_date - item.ini_date
                days, seconds = diff.days, diff.seconds
                hours += seconds // 3600
                minutes += (seconds % 3600) // 60

        if minutes > 59:
            hours += minutes // 60
            minutes = minutes % 60
        return hours, minutes
    
    def worked_time_shifts(self, ini_date, end_date):
        idate = "{} 00:00".format(ini_date)
        edate = "{} 23:59".format(end_date)
        item_list = self.workdays.filter(ini_date__gte=idate, end_date__lte=edate)
        hours_mornig = 0
        minutes_morning = 0
        hours_afternoon = 0
        minutes_afternoon = 0
        for item in item_list:
            if item.finish:
                diff_seconds = (item.end_date - item.ini_date).total_seconds()
                if item.ini_date.hour < 14 and item.ini_date.hour >= 6:
                    hours_morning += diff_seconds // 3600
                    minutes_morning += ((diff_seconds % 3600) / 60)
                else:
                    hours_afternoon += diff_seconds // 3600
                    minutes_afternoon += ((diff_seconds % 3600) / 60)

        return hours_mornig, minutes_morning, hours_afternoon, minutes_afternoon


    def get_qr_uuid(self):
        if len(self.uuid) < 10 :
            temp_uuid = str(uuid.uuid4())
            while Employee.objects.filter(uuid=temp_uuid).exists():
                temp_uuid = str(uuid.uuid4())
            self.uuid = temp_uuid
            self.save()
        data = reverse ('pwa-check-clock', kwargs={'uuid': self.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        img_data = generate_qr_image(data, self.comp.logo.path)
        return img_data

    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')

'''
    WORKDAY
'''
class Workday(models.Model):
    finish = models.BooleanField(default=False, verbose_name=_('Terminada'));
    ini_date = models.DateTimeField(default=timezone.now, null=True, verbose_name=_('Inicio'))
    end_date = models.DateTimeField(default=timezone.now, null=True, verbose_name=_('Fin'))
    employee = models.ForeignKey(Employee, verbose_name=_('Empleado'), on_delete=models.CASCADE, null=True, related_name="workdays")
    ipaddress = models.GenericIPAddressField(verbose_name=_('IP Address'), null=True, blank=True)
    ipaddress_out = models.GenericIPAddressField(verbose_name=_('IP Address Out'), null=True, blank=True)

    def can_user_response(self, user):
        try:
            pending = self.modifications.filter(status=0)
            if not pending.exists():
                return False
            return pending.first().can_user_response(user)

        except Exception as e:
            print(show_exc(e))
        return False
            
    @property
    def duration(self):
        edate = self.end_date.replace(microsecond=0) 
        idate = self.ini_date.replace(microsecond=0)
        diff = edate - idate
        days, seconds = diff.days, diff.seconds
        return (diff.total_seconds())

    @property
    def extraday(self):
        if self.end_date.date() > self.ini_date.date():
            diff_days = self.end_date.date().day - self.ini_date.date().day
            return f"(+{diff_days}d)"
        return ""
    
    @property
    def in_morning(self):
        local_time = localtime(self.ini_date)
        if local_time.hour < 14 and local_time.hour >= 6:
            return True
        return False
    
    @property
    def in_afternoon(self):
        if localtime(self.ini_date).hour >= 14 or localtime(self.ini_date).hour < 6:
            return True
        return False
    
    @property
    def status_label(self):
        modifications = self.modifications.all().order_by('-mod_date')
        labels = ['pending', 'accepted', 'rejected']
        if modifications.exists():
            mod = modifications.first()
            return labels[mod.status]
        return ""

    @property
    def modifications_pending(self):
        modifications = self.modifications.filter(status=0)
        return modifications.exists()
    
    @property
    def get_ini_date(self):
        modifications_accepted = self.modifications.filter(status=1).order_by('-mod_date')
        if modifications_accepted.exists():
            mod = modifications_accepted.first()
            return mod.ini_date
        return self.ini_date
    
    @property
    def get_end_date(self):
        modifications_accepted = self.modifications.filter(status=1).order_by('-mod_date')
        if modifications_accepted.exists():
            mod = modifications_accepted.first()
            return mod.end_date
        return self.end_date
    
    @property
    def get_duration(self):
        modifications_accepted = self.modifications.filter(status=1).order_by('-mod_date')
        if modifications_accepted.exists():
            mod = modifications_accepted.first()
            return mod.duration
        else:
            return self.duration

            
    
    def setIpAddress(self, request):
        ipaddress = "127.0.0.1"
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ipaddress = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
        else:
            ipaddress = request.META.get('REMOTE_ADDR', None)
        if self.finish:
            self.ipaddress_out = ipaddress
        else:
            self.ipaddress = ipaddress
 
    class Meta:
        verbose_name = _('Asistencia')
        verbose_name_plural = _('Asistencias')


class WorkdayModification(models.Model):
    workday = models.ForeignKey(Workday, verbose_name=_('Asistencia'), on_delete=models.CASCADE, null=True, related_name="modifications")
    mod_date = models.DateTimeField(auto_now=True, null=True, verbose_name=_('Fecha modificación')) # Autodate
    evaluation_date = models.DateTimeField(default=timezone.now, null=True, verbose_name=_('Fecha evaluación'))
    ini_date = models.DateTimeField(default=timezone.now, null=True, verbose_name=_('Fecha inicio nueva'))
    end_date = models.DateTimeField(default=timezone.now, null=True, verbose_name=_('Fecha fin nueva'))
    reason = models.CharField(max_length=255, verbose_name = _('Motivo'), default="")
    requested_by = models.ForeignKey(User, verbose_name=_('Modificado por'), on_delete=models.SET_NULL, null=True, related_name="workday_modifications")
    accepted_by = models.ForeignKey(User, verbose_name=_('Aceptado por'), on_delete=models.SET_NULL, null=True, blank=True, related_name="workday_modifications_accepted")
    status = models.IntegerField(verbose_name = _('Estado'), default=0, choices=((0, 'Pendiente'), (1, 'Aceptada'), (2, 'Rechazada')))

    @property
    def duration(self):
        try:
             edate = self.end_date.replace(microsecond=0) 
             idate = self.ini_date.replace(microsecond=0)
             diff = edate - idate
             days, seconds = diff.days, diff.seconds
             return (diff.total_seconds())
        except Exception as e:
            print (show_exc(e))
            return 0

    @property
    def extraday(self):
        if self.end_date.date() > self.ini_date.date():
            diff_days = self.end_date.date().day - self.ini_date.date().day
            return f"(+{diff_days}d)"
        return ""
    
    @property
    def in_morning(self):
        local_time = localtime(self.ini_date)
        if local_time.hour < 14 and local_time.hour >= 6:
            return True
        return False
    
    @property
    def in_afternoon(self):
        if localtime(self.ini_date).hour >= 14 or localtime(self.ini_date).hour < 6:
            return True
        return False
    
    @property
    def requested_user(self):
        if self.requested_by == self.workday.employee.user:
            return _('Empleado')
        else:
            return _('Empresa')
        
    def can_user_response(self, user):
        if user == self.requested_by:
            return False
        employee_comp = self.workday.employee.comp
        manager = Manager.objects.filter(user=self.requested_by, comp=employee_comp)
        if not manager.exists():
            return False
        return True

    class Meta:
        verbose_name = _('Modificación de asistencia')
        verbose_name_plural = _('Modificaciones de asistencias')
        ordering = ['-mod_date']
