# Generate a form for the Company model
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Company, Manager, Employee
import re

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'logo', 'nif', 'last_payment_amount', 'last_payment', 'expiration_date', 'ccc', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            
        }
        labels = {
            'name': _('Nombre'),
            'logo': _('Logo'),
            'nif': _('NIF'),
        }
        help_texts = {
            'name': _('Nombre de la empresa'),
            'logo': _('Selecciona el archivo a subir'),
            'nif': _('Número de identificación fiscal'),
            'last_payment_amount': _('Último importe pagado'),
            'last_payment': _('Fecha del último pago'),
            'expiration_date': _('Fecha de expiración'),
            'ccc': _('Código Cuenta Cotización'),
            'address': _('Dirección del centro de trabajo'),
        }
        error_messages = {
            'name': {
                'required': _('Este campo es obligatorio.'),
            },
            'logo': {
                'invalid': _('El archivo no es válido.'),
            },
            'nif': {
                'required': _('Este campo es obligatorio.'),
            },
            'last_payment_amount': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El importe del último pago no es válido.'),
            },
            'last_payment': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('La fecha del último pago no es válida.'),
            },

            'expiration_date': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('La fecha de expiración no es válida.'),
            },
            'ccc': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El código de cuenta de cotización no es válido.'),
            },
            'address': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('La dirección no es válida.'),
            },
        }
    # Add custom validation for the logo field
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Check if the file is an image
            if not logo.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                raise forms.ValidationError(_('El archivo debe ser una imagen.'))
            # Check the file size (5MB limit)
            if logo.size > 5 * 1024 * 1024:
                raise forms.ValidationError(_('El tamaño del archivo no puede ser mayor de 5MB.'))
        return logo
    
    # Add custom validation for the NIF field
    def clean_nif(self):
        nif = self.cleaned_data.get('nif')
        if not nif:
            raise forms.ValidationError(_('El NIF es obligatorio.'))
        # Validar con regex el formato básico del NIF español
        if not re.match(r'^[0-9]{8}[A-Z]$', nif.upper()) and not re.match(r'^[XYZ][0-9]{7}[A-Z]$', nif.upper()) and not re.match(r'^[A-Z][0-9]{7,8}$', nif.upper()):
            raise forms.ValidationError(_('El NIF no es válido.'))
        return nif.upper()
        

class ManagerForm(forms.ModelForm):

    # Custom validation for the pin field
    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        comp = self.cleaned_data.get('comp')
        if Manager.objects.filter(pin=pin, comp=comp).exists():
            raise forms.ValidationError(_('Ya existe un gerente con este PIN para esta empresa.'))
        return pin

    class Meta:
        model = Manager
        fields = ['name', 'email', 'phone', 'pin', 'comp', 'user', 'dni']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'pin': forms.TextInput(attrs={'class': 'form-control'}),
            'comp': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': _('Nombre'),
            'email': _('Email'),
            'phone': _('Teléfono'),
        }
        help_texts = {
            'name': _('Nombre del gerente'),
            'email': _('Email del gerente'),
            'phone': _('Teléfono del gerente'),
        }
        error_messages = {
            'name': {
                'required': _('Este campo es obligatorio.'),
            },
            'email': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El email no es válido.'),
            },
            'phone': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El teléfono no es válido.'),
            },
            'pin': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El PIN no es válido.'),
            },
            'comp': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('La empresa no es válida.'),
            },
            'dni': {
                'required': _('Este campo es obligatorio.'),
                'invalid': _('El DNI no es válido.'),
            },
            'email': {
                'invalid': _('El email no es válido.'),
            },
        }
