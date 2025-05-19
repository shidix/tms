from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext_lazy as _ 
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

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name = _('Nombre'))
    logo = models.ImageField(upload_to=upload_logo, blank=True, verbose_name="Logo", help_text="Select file to upload")
    qr = models.ImageField(upload_to=upload_qr, blank=True, verbose_name="QR", help_text="Select file to upload")
    nif = models.CharField(max_length=20, verbose_name = _('NIF'), default="")
    uuid = models.CharField(max_length=200, verbose_name = _('UUID'), default="")

    def __str__(self):
        return self.name
    
    @property
    def employees(self):
        return Employee.objects.filter(comp=self)
    
    @property
    def view_logo(self):
        if self.logo:
            return format_html('<img src="{}" class="w-75 text-center"/>', self.logo.url)
        return "-"

    @property
    def get_qr_login(self):
        data = reverse ('pwa-company-login', kwargs={'uuid': self.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        logo = Image.open(self.logo.path)
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
                self.user.username = self.email
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
        #item_list = self.assistances.filter(ini_date__gte=ini_date, end_date__lte=end_date)
        hours = 0
        minutes = 0
        for item in item_list:
            if item.finish:
                diff = item.end_date - item.ini_date
                days, seconds = diff.days, diff.seconds
                hours += seconds // 3600
                minutes += (seconds % 3600) // 60
                #hours = days * 24 + seconds // 3600
                #seconds = seconds % 60
        if minutes > 59:
            hours += minutes // 60
            minutes = minutes % 60
        return hours, minutes
        #return "{}:{}".format(hours, minutes) 
        #return "{} horas y {}  minutos".format(hours, minutes) 

    def get_qr_uuid(self):
        if len(self.uuid) < 10 :
            temp_uuid = str(uuid.uuid4())
            while Employee.objects.filter(uuid=temp_uuid).exists():
                temp_uuid = str(uuid.uuid4())
            self.uuid = temp_uuid
            self.save()
        data = reverse ('pwa-check-clock', kwargs={'uuid': self.uuid})
        data = "{}{}".format(settings.MAIN_URL, data)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        logo = Image.open(self.comp.logo.path)
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

    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')

'''
    WORKDAY
'''
class Workday(models.Model):
    finish = models.BooleanField(default=False, verbose_name=_('Terminada'));
    ini_date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Inicio'))
    end_date = models.DateTimeField(default=datetime.datetime.now(), null=True, verbose_name=_('Fin'))
    employee = models.ForeignKey(Employee, verbose_name=_('Empleado'), on_delete=models.CASCADE, null=True, related_name="workdays")

    @property
    def duration(self):

        edate = self.end_date.replace(microsecond=0) 
        idate = self.ini_date.replace(microsecond=0)
        diff = edate - idate
        days, seconds = diff.days, diff.seconds
        return (diff.total_seconds())
        #hours += seconds // 3600
        #minutes += (seconds % 3600) // 60
        #if minutes > 59:
        #    hours += minutes // 60
        #    minutes = minutes % 60
        #return hours, minutes

    @property
    def extraday(self):
        if self.end_date.date() > self.ini_date.date():
            diff_days = self.end_date.date().day - self.ini_date.date().day
            return f"(+{diff_days}d)"
        return ""
 
    class Meta:
        verbose_name = _('Asistencia')
        verbose_name_plural = _('Asistencias')


