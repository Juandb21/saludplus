# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import time, datetime, date

class Paciente(models.Model):
    nombre_completo = models.CharField(max_length=100)
    documento_identidad = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^\d+$', 'Solo se permiten números')]
    )
    telefono = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[\d\-\+\(\)\s]+$', 'Formato de teléfono inválido')]
    )
    correo = models.EmailField()
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_completo} - {self.documento_identidad}"
    
    def get_edad(self):
        """Calcula la edad actual del paciente"""
        if self.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - self.fecha_nacimiento.year
            if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
                edad -= 1
            return edad
        return None
    
    def es_menor_de_edad(self):
        """Retorna True si el paciente es menor de 18 años"""
        edad = self.get_edad()
        return edad is not None and edad < 18

    class Meta:
        ordering = ['nombre_completo']


class Doctor(models.Model):
    ESPECIALIDADES = [
        ('medicina_general', 'Medicina General'),
        ('pediatria', 'Pediatría'),
        ('odontologia', 'Odontología'),
    ]

    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=50, choices=ESPECIALIDADES)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.nombre} - {self.get_especialidad_display()}"

    class Meta:
        ordering = ['nombre']


class HorarioAtencion(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.doctor.nombre} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['doctor', 'dia_semana']


class Cita(models.Model):
    ESTADOS = [
        ('programada', 'Programada'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.paciente.nombre_completo} - {self.doctor.nombre} - {self.fecha} {self.hora}"

    class Meta:
        ordering = ['-fecha', '-hora']
        unique_together = ['doctor', 'fecha', 'hora']
