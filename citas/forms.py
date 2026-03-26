# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from .models import Paciente, Doctor, Cita, HorarioAtencion
from datetime import datetime, timedelta

class LoginFormulario(forms.Form):
    TIPO_USUARIO = [
        ('personal', 'Personal'),
        ('paciente', 'Paciente'),
    ]
    
    tipo_usuario = forms.ChoiceField(choices=TIPO_USUARIO, widget=forms.RadioSelect())
    usuario = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingrese su usuario'
    }))
    contraseña = forms.CharField(required=False, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingrese su contraseña'
    }))
    cedula = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingrese su número de cédula'
    }))


class PacienteFormulario(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre_completo', 'documento_identidad', 'telefono', 'correo', 'fecha_nacimiento']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Juan Pérez García'
            }),
            'documento_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '555-0123'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'paciente@email.com'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer fecha_nacimiento obligatoria
        self.fields['fecha_nacimiento'].required = True
        self.fields['fecha_nacimiento'].label = 'Fecha de Nacimiento *'
        # Agregar clase Bootstrap al widget
        self.fields['fecha_nacimiento'].widget.attrs['class'] = 'form-control'
        self.fields['fecha_nacimiento'].widget.attrs['type'] = 'date'
    
    def clean_fecha_nacimiento(self):
        """Validar que la fecha de nacimiento no sea en el futuro"""
        from datetime import date
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento and fecha_nacimiento > date.today():
            raise forms.ValidationError('La fecha de nacimiento no puede ser en el futuro.')
        return fecha_nacimiento


class BuscarPacienteFormulario(forms.Form):
    documento = forms.CharField(
        label='Número de Cédula',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su número de cédula'
        })
    )


class BuscarDoctorFormulario(forms.Form):
    nombre = forms.CharField(
        label='Nombre del Médico',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del médico'
        })
    )


class AgendarCitaFormulario(forms.ModelForm):
    fecha = forms.DateField(
        label='Fecha',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'fecha', 'hora']
        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hora': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.all()
        self.fields['doctor'].queryset = Doctor.objects.filter(activo=True)
