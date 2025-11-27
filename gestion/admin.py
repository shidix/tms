from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from tms.commons import generate_qr as gen_qr
from .models import *

import os


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'nif', 'view_logo', 'view_qr')

    def view_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="20%"/>', obj.logo.url)
        return "-"
    view_logo.short_description = "Logo"

    def view_qr(self, obj):
        url = reverse('admin:renew_qr', args=[obj.pk])
        if obj.qr:
            return format_html('<img src="{}" width="20%"/><br/><a href="{}">Regenerar QR</a>', obj.qr.url, url)
        return format_html('<a href="{}">Generar QR</a>', url)
    view_qr.short_description = "QR"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [ path('renew_qr/<int:obj_id>/', self.admin_site.admin_view(self.renew_qr), name='renew_qr'), ]
        return custom_urls + urls

    def renew_qr(self, request, obj_id):
        obj = self.get_object(request, obj_id)
        if obj.qr:
            obj.qr.delete(save=True)

        url = "{}/gestion/workdays/journey/{}".format(settings.ADMIN_URL, obj.id)
        path = "{}{}".format(settings.BASE_DIR, obj.logo.url) if obj.logo else ""
        img_data = ContentFile(gen_qr(url, path))
        obj.qr.save('qr_{}.png'.format(obj.id), img_data, save=True)

        messages.success(request, f'QR generado: {obj.name}')
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

class ManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'comp')

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'comp')

class WorkdayModificationAdmin(admin.ModelAdmin):
    list_display = ('initial_ini_date', 'initial_end_date', 'requested_by', 'ini_date', 'end_date', 'reason', 'status', 'mod_date')
    list_filter = ('status', 'mod_date')
    search_fields = ('workday__employee__name', 'requested_by__username', 'reason')

    def initial_ini_date(self, obj):
        return obj.workday.ini_date
    initial_ini_date.short_description = "Inicio original"
    def initial_end_date(self, obj):
        return obj.workday.end_date
    initial_end_date.short_description = "Fin original"
admin.site.register(WorkdayModification, WorkdayModificationAdmin)

#
#class WasteInFacilityAdmin(admin.ModelAdmin):
#    list_display = ('code', 'facility', 'waste', 'filling_degree', 'toRoute')
#    list_filter = ('facility',)
#
admin.site.register(Company, CompanyAdmin)
admin.site.register(Manager, ManagerAdmin)
admin.site.register(Employee, EmployeeAdmin)
#
