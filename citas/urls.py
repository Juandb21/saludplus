# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Recepción
    path('recepcion/', views.recepcion, name='recepcion'),
    path('recepcion/consultar-citas/', views.consultar_citas, name='consultar_citas'),
    path('recepcion/registrar-paciente/', views.registrar_paciente, name='registrar_paciente'),
    path('recepcion/agendar-cita/', views.agendar_cita, name='agendar_cita'),
    path('recepcion/editar-cita/<int:cita_id>/', views.editar_cita, name='editar_cita'),
    path('recepcion/eliminar-cita/<int:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
    
    # Doctor
    path('mi-agenda/', views.mi_agenda, name='mi_agenda'),
    
    # Administrador
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    
    # Paciente
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    
    # API
    path('api/obtener-horas/', views.obtener_horas_disponibles, name='obtener_horas'),
    path('api/buscar-doctores/', views.buscar_doctores, name='buscar_doctores'),
    path('api/buscar-pacientes/', views.buscar_pacientes, name='buscar_pacientes'),
]
