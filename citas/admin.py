# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Paciente, Doctor, HorarioAtencion, Cita


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'documento_identidad', 'telefono', 'correo', 'fecha_creacion')
    search_fields = ('nombre_completo', 'documento_identidad')
    list_filter = ('fecha_creacion',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'activo', 'fecha_creacion')
    search_fields = ('nombre',)
    list_filter = ('especialidad', 'activo', 'fecha_creacion')


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'dia_semana', 'hora_inicio', 'hora_fin')
    search_fields = ('doctor__nombre',)
    list_filter = ('dia_semana',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha', 'hora', 'estado', 'fecha_creacion')
    search_fields = ('paciente__nombre_completo', 'doctor__nombre')
    list_filter = ('estado', 'fecha', 'doctor')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
