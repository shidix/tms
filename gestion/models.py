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
        scale = 0.5**0.5
        logo_size = (int(logo.size[0] * scale), int(logo.size[1] * scale))
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
                return format_html('<img src="{}" class="w-75 text-center mx-auto"/>', self.logo.url)
            return format_html('<img src="{}" class="w-25 text-center mx-auto"/>', '/static/images/logo-fichaje.png')
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
    comp = models.ForeignKey(Company, verbose_name=_("Empresa"), on_delete=models.SET_NULL, blank=True, null=True)
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")

    def __str__(self):
        return self.name

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
    name = models.CharField(max_length=200, verbose_name = _('Razón Social'), default="")
    phone = models.CharField(max_length=20, verbose_name = _('Teléfono de contacto'), null=True, default = '0000000000')
    weekly_hours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Horas por semana'), default=40.00)
    affiliation_number = models.CharField(max_length=20, verbose_name=_('Número de afiliación'), default="")
    email = models.EmailField(verbose_name = _('Email de contacto'), default="", null=True)
    user = models.OneToOneField(User, verbose_name='Usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='employee')
    comp = models.ForeignKey(Company, verbose_name=_("Empresa"), on_delete=models.SET_NULL, blank=True, null=True)
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")

    def __str__(self):
        return self.name

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


