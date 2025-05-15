# Generate a form for the Company model
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'logo', 'nif']
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

