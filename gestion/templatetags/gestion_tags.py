from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static
import string, random

register = template.Library()

'''
    Filters
'''
@register.filter
def in_group(user, group):
    try:
        return user.groups.filter(name=group).exists()
    except:
        return False

@register.filter
def random_str(nchars='128'):
    try:
        n = int(nchars)
    except:
        n = 128
    return (''.join(random.choice(string.ascii_letters) for i in range(n)))

@register.filter
def addstr(arg1,arg2):
    return(mark_safe(str(arg1)+str(arg2)))

@register.filter
def comp_logo(user, company=None):
    try:
        return user.manager.comp.logo.url
    except:
        try:
            return user.employee.comp.logo.url
        except:
            try:
                return company.logo.url
            except:
                return static("/images/logo-fichaje.png")

'''
    Simple Tags
'''
@register.simple_tag(takes_context=True)
def current(context, url, **kwargs):
    try:
        request = context['request']
        #if request.get_full_path().startswith(reverse(url)) :
        if url in request.get_full_path():
            return "active"
        else:
            return ""
    except:
        return ""

@register.simple_tag()
def get_worked_time(emp, ini_date, end_date):
    hours, minutes = emp.worked_time(ini_date, end_date)
    return "{} horas y {} minutos".format(hours, minutes)

@register.filter
def local_time(mydate):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if mydate != "":
        utc_now = mydate.replace(tzinfo=ZoneInfo("UTC"))
        canary_time = utc_now.astimezone(ZoneInfo("Atlantic/Canary"))
        canary_time = canary_time.replace(tzinfo=ZoneInfo("UTC"))
        return canary_time
    return mydate

@register.filter
def toDuration(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@register.filter
def extraday(seconds):
    if seconds > 86400:
        return f"(+{seconds // 86400}d)"
    else:
        return ""

