# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import Paciente, Doctor, Cita, HorarioAtencion
from .forms import (
    LoginFormulario, PacienteFormulario, BuscarPacienteFormulario,
    BuscarDoctorFormulario, AgendarCitaFormulario
)


def hora_en_punto(hora):
    """Permite solo horas fijas, por ejemplo 08:00, 14:00."""
    return hora.minute == 0 and hora.second == 0


def es_hora_futura(fecha, hora):
    """Valida que una fecha/hora no esté en el pasado."""
    return datetime.combine(fecha, hora) > datetime.now()


def index(request):
    """Página de inicio"""
    return render(request, 'citas/index.html')


def obtener_destino_usuario(user):
    """Determina la vista inicial según el rol del usuario autenticado."""
    if user.is_superuser:
        return 'admin_panel'
    if user.groups.filter(name='Recepcionista').exists():
        return 'recepcion'
    if user.groups.filter(name='Doctor').exists():
        return 'mi_agenda'
    if user.groups.filter(name='Administrador').exists():
        return 'admin_panel'
    return None


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        destino = obtener_destino_usuario(request.user)
        if destino:
            return redirect(destino)

        # Evita sesiones activas de usuarios sin rol asignado.
        logout(request)
        messages.error(request, 'Tu usuario no tiene un rol asignado. Contacta al administrador.')

    if request.method == 'POST':
        form = LoginFormulario(request.POST)
        if form.is_valid():
            tipo_usuario = form.cleaned_data['tipo_usuario']
            
            if tipo_usuario == 'personal':
                usuario = form.cleaned_data['usuario']
                contraseña = form.cleaned_data['contraseña']
                
                user = authenticate(request, username=usuario, password=contraseña)
                if user is not None:
                    destino = obtener_destino_usuario(user)
                    if destino:
                        login(request, user)
                        return redirect(destino)

                    form.add_error(None, 'Usuario sin rol asignado. Contacta al administrador.')
                else:
                    form.add_error(None, 'Usuario o contraseña incorrectos')
            
            elif tipo_usuario == 'paciente':
                cedula = form.cleaned_data['cedula']
                try:
                    paciente = Paciente.objects.get(documento_identidad=cedula)
                    request.session['paciente_id'] = paciente.id
                    return redirect('mis_citas')
                except Paciente.DoesNotExist:
                    form.add_error(None, 'Paciente no encontrado. Por favor, acérquese a recepción.')
    else:
        form = LoginFormulario()
    
    return render(request, 'citas/login.html', {'form': form})


def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    if 'paciente_id' in request.session:
        del request.session['paciente_id']
    return redirect('index')


@login_required
def recepcion(request):
    """Panel de recepción"""
    user = request.user
    
    # Verificar que es recepcionista
    if not user.groups.filter(name='Recepcionista').exists():
        return redirect('index')
    
    # Estadísticas
    citas_hoy = Cita.objects.filter(
        fecha=datetime.now().date(),
        estado__in=['programada', 'confirmada']
    ).count()
    
    total_pacientes = Paciente.objects.count()
    medicos_activos = Doctor.objects.filter(activo=True).count()
    medicos_disponibles = Doctor.objects.filter(activo=True).order_by('nombre')
    pacientes_disponibles = Paciente.objects.all().order_by('nombre_completo')
    
    # Todas las citas
    todas_citas = Cita.objects.all().select_related('paciente', 'doctor')
    
    context = {
        'citas_hoy': citas_hoy,
        'total_pacientes': total_pacientes,
        'medicos_activos': medicos_activos,
        'todas_citas': todas_citas,
        'medicos_disponibles': medicos_disponibles,
        'pacientes_disponibles': pacientes_disponibles,
    }
    
    return render(request, 'citas/recepcion.html', context)


def consultar_citas(request):
    """Consultar citas del paciente autenticado"""
    # Verificar si es paciente autenticado
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('index')
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    citas = paciente.citas.all().order_by('-fecha', '-hora')
    
    context = {
        'paciente': paciente,
        'citas': citas,
    }
    
    return render(request, 'citas/consultar_citas.html', context)


@login_required
def registrar_paciente(request):
    """Registrar un nuevo paciente"""
    user = request.user
    if not user.groups.filter(name='Recepcionista').exists():
        return redirect('index')
    
    if request.method == 'POST':
        form = PacienteFormulario(request.POST)
        if form.is_valid():
            form.save()
            return redirect('recepcion')
    else:
        form = PacienteFormulario()
    
    return render(request, 'citas/registrar_paciente.html', {'form': form})


@login_required
def agendar_cita(request):
    """Agendar una nueva cita"""
    user = request.user
    if not user.groups.filter(name='Recepcionista').exists():
        return redirect('index')
    
    paciente = None
    doctor = None
    horas_disponibles = []
    
    if request.method == 'POST':
        # Buscar paciente
        cedula = (request.POST.get('cedula_paciente') or '').strip()
        paciente_id = request.POST.get('paciente_id')
        nombre_doctor = request.POST.get('nombre_doctor')
        doctor_id = request.POST.get('doctor_id')
        fecha_str = request.POST.get('fecha')
        hora = request.POST.get('hora')
        fecha = None

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'La fecha ingresada no es válida.')
                return redirect('recepcion')

            if fecha < datetime.now().date():
                messages.error(request, 'No se pueden agendar citas en fechas pasadas.')
                return redirect('recepcion')
        
        if paciente_id:
            try:
                paciente = Paciente.objects.get(id=paciente_id)
            except Paciente.DoesNotExist:
                paciente = None
        elif cedula:
            try:
                paciente = Paciente.objects.get(documento_identidad=cedula)
            except Paciente.DoesNotExist:
                paciente = Paciente.objects.filter(nombre_completo__icontains=cedula).first()
        
        if doctor_id:
            try:
                doctor_obj = Doctor.objects.get(id=doctor_id, activo=True)
                # Si el paciente es menor de edad, solo permitir pediatría
                if paciente and paciente.es_menor_de_edad():
                    if doctor_obj.especialidad == 'pediatria':
                        doctor = doctor_obj
                    else:
                        messages.error(request, 'Solo se puede agendar cita con pediatría para menores de edad.')
                        doctor = None
                else:
                    doctor = doctor_obj
            except Doctor.DoesNotExist:
                doctor = None
        elif nombre_doctor:
            # Filtrar doctores según la edad del paciente
            doctores_query = Doctor.objects.filter(
                nombre__icontains=nombre_doctor,
                activo=True
            )
            
            # Si el paciente es menor de edad, solo permitir pediatría
            if paciente and paciente.es_menor_de_edad():
                doctores_query = doctores_query.filter(especialidad='pediatria')
            
            if doctores_query.exists():
                doctor = doctores_query.first()
        
        # Si tenemos fecha y doctor, calcular horas disponibles
        if fecha and doctor:
            dia_semana = fecha.weekday()
            
            # Obtener horario del doctor para ese día
            horarios = doctor.horarios.filter(dia_semana=dia_semana)
            
            if horarios.exists():
                horario = horarios.first()
                horas_disponibles = generar_horas_disponibles(doctor, fecha, horario)
        
        # Si tenemos todos los datos, agendar
        if paciente and doctor and fecha and hora:
            hora_obj = datetime.strptime(hora, '%H:%M').time()

            if not es_hora_futura(fecha, hora_obj):
                messages.error(request, 'Solo puedes agendar horas futuras para el día de hoy.')
                return redirect('recepcion')
            
            # Verificar que la hora está disponible
            if not Cita.objects.filter(doctor=doctor, fecha=fecha, hora=hora_obj).exists():
                cita = Cita.objects.create(
                    paciente=paciente,
                    doctor=doctor,
                    fecha=fecha,
                    hora=hora_obj
                )
                return redirect('recepcion')
    
    # Obtener lista de todos los pacientes y doctores para el dropdown
    todos_pacientes = Paciente.objects.all().order_by('nombre_completo')
    todos_doctores = Doctor.objects.filter(activo=True).order_by('nombre')
    
    # Si hay paciente seleccionado, filtrar doctores según su edad
    if paciente:
        if paciente.es_menor_de_edad():
            # Solo pediatría para menores
            todos_doctores = todos_doctores.filter(especialidad='pediatria')
    
    context = {
        'paciente': paciente,
        'doctor': doctor,
        'horas_disponibles': horas_disponibles,
        'todos_pacientes': todos_pacientes,
        'todos_doctores': todos_doctores,
    }
    
    return render(request, 'citas/agendar_cita.html', context)


def generar_horas_disponibles(doctor, fecha, horario):
    """Generar horas disponibles para un doctor en una fecha"""
    horas_disponibles = []
    hora_actual = horario.hora_inicio
    duracion_cita = timedelta(minutes=30)
    
    # Obtener citas existentes para ese día
    citas_existentes = Cita.objects.filter(
        doctor=doctor,
        fecha=fecha
    ).values_list('hora', flat=True)
    
    while hora_actual < horario.hora_fin:
        if hora_actual not in citas_existentes and es_hora_futura(fecha, hora_actual):
            horas_disponibles.append(hora_actual.strftime('%H:%M'))
        
        # Sumar 30 minutos
        hora_datetime = datetime.combine(fecha, hora_actual)
        hora_datetime += duracion_cita
        hora_actual = hora_datetime.time()
    
    return horas_disponibles


@login_required
def mi_agenda(request):
    """Agenda del doctor"""
    user = request.user
    if not user.is_superuser and not user.groups.filter(name='Doctor').exists():
        return redirect('index')
    
    try:
        doctor = Doctor.objects.get(usuario=user)
    except Doctor.DoesNotExist:
        return redirect('index')
    
    # Obtener fecha seleccionada (por defecto hoy)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha = datetime.now().date()
    
    # Obtener horario del doctor para ese día
    dia_semana = fecha.weekday()
    horarios = doctor.horarios.filter(dia_semana=dia_semana)
    horarios_doctor = doctor.horarios.all().order_by('dia_semana')
    
    if horarios.exists():
        horas_disponibles = generar_horas_disponibles(doctor, fecha, horarios.first())
    else:
        horas_disponibles = []
    
    # Obtener citas del día
    citas_dia = doctor.citas.filter(fecha=fecha).order_by('hora')
    
    context = {
        'doctor': doctor,
        'fecha': fecha,
        'horas_disponibles': horas_disponibles,
        'citas_dia': citas_dia,
        'horarios': horarios,
        'horarios_doctor': horarios_doctor,
    }
    
    return render(request, 'citas/mi_agenda.html', context)


@login_required
def admin_panel(request):
    """Panel de administración"""
    user = request.user
    if not user.is_superuser and not user.groups.filter(name='Administrador').exists():
        return redirect('index')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_doctor':
            nombre = (request.POST.get('nombre') or '').strip()
            especialidad = (request.POST.get('especialidad') or '').strip()
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''

            if not nombre or not especialidad or not username or not password:
                messages.error(request, 'Debe completar nombre, especialidad, usuario y contraseña del médico.')
                return redirect('admin_panel')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe. Elija otro usuario para el médico.')
                return redirect('admin_panel')

            if len(password) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return redirect('admin_panel')

            nombres = nombre.split(' ', 1)
            first_name = nombres[0]
            last_name = nombres[1] if len(nombres) > 1 else ''

            with transaction.atomic():
                user_doctor = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                doctor_group, _ = Group.objects.get_or_create(name='Doctor')
                user_doctor.groups.add(doctor_group)

                doctor = Doctor.objects.create(
                    nombre=nombre,
                    especialidad=especialidad,
                    usuario=user_doctor,
                    activo=True,
                )

            dias = request.POST.getlist('dia_semana[]')
            horas_inicio = request.POST.getlist('hora_inicio[]')
            horas_fin = request.POST.getlist('hora_fin[]')

            horarios_creados = 0
            for dia, hora_inicio_str, hora_fin_str in zip(dias, horas_inicio, horas_fin):
                if not dia or not hora_inicio_str or not hora_fin_str:
                    continue

                try:
                    dia_semana = int(dia)
                    hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                    hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
                except (ValueError, TypeError):
                    continue

                if hora_inicio >= hora_fin:
                    continue

                if not hora_en_punto(hora_inicio) or not hora_en_punto(hora_fin):
                    continue

                HorarioAtencion.objects.update_or_create(
                    doctor=doctor,
                    dia_semana=dia_semana,
                    defaults={'hora_inicio': hora_inicio, 'hora_fin': hora_fin}
                )
                horarios_creados += 1

            if horarios_creados:
                messages.success(request, f'Médico registrado con {horarios_creados} horario(s).')
            else:
                messages.success(request, 'Médico registrado correctamente.')

            return redirect('admin_panel')

        if action == 'create_recepcionista':
            nombre = (request.POST.get('nombre') or '').strip()
            correo = (request.POST.get('correo') or '').strip()
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''

            if not nombre or not correo or not username or not password:
                messages.error(request, 'Debe completar nombre, correo, usuario y contraseña del recepcionista.')
                return redirect('admin_panel')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe. Elija otro usuario para el recepcionista.')
                return redirect('admin_panel')

            if len(password) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return redirect('admin_panel')

            nombres = nombre.split(' ', 1)
            first_name = nombres[0]
            last_name = nombres[1] if len(nombres) > 1 else ''

            with transaction.atomic():
                recep_user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=correo,
                    first_name=first_name,
                    last_name=last_name,
                )

                recep_group, _ = Group.objects.get_or_create(name='Recepcionista')
                recep_user.groups.add(recep_group)

            messages.success(request, 'Recepcionista creado correctamente.')
            return redirect('admin_panel')

        if action == 'create_horario':
            doctor_id = request.POST.get('doctor_id')
            dia = request.POST.get('dia_semana')
            hora_inicio_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')

            if not doctor_id or not dia or not hora_inicio_str or not hora_fin_str:
                messages.error(request, 'Debe completar día y rango de horas para agregar horario.')
                return redirect('admin_panel')

            doctor = get_object_or_404(Doctor, id=doctor_id)

            try:
                dia_semana = int(dia)
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
            except (ValueError, TypeError):
                messages.error(request, 'Formato de día u hora inválido.')
                return redirect('admin_panel')

            if hora_inicio >= hora_fin:
                messages.error(request, 'La hora de inicio debe ser menor que la hora de fin.')
                return redirect('admin_panel')

            if not hora_en_punto(hora_inicio) or not hora_en_punto(hora_fin):
                messages.error(request, 'Solo se permiten horas en punto, por ejemplo 08:00 o 16:00.')
                return redirect('admin_panel')

            HorarioAtencion.objects.update_or_create(
                doctor=doctor,
                dia_semana=dia_semana,
                defaults={'hora_inicio': hora_inicio, 'hora_fin': hora_fin}
            )
            messages.success(request, 'Horario agregado/actualizado correctamente.')
            return redirect('admin_panel')

        if action == 'update_horario':
            horario_id = request.POST.get('horario_id')
            hora_inicio_str = request.POST.get('hora_inicio')
            hora_fin_str = request.POST.get('hora_fin')

            if not horario_id or not hora_inicio_str or not hora_fin_str:
                messages.error(request, 'Debe completar hora de inicio y fin para actualizar horario.')
                return redirect('admin_panel')

            horario = get_object_or_404(HorarioAtencion, id=horario_id)

            try:
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
            except (ValueError, TypeError):
                messages.error(request, 'Formato de hora inválido.')
                return redirect('admin_panel')

            if hora_inicio >= hora_fin:
                messages.error(request, 'La hora de inicio debe ser menor que la hora de fin.')
                return redirect('admin_panel')

            if not hora_en_punto(hora_inicio) or not hora_en_punto(hora_fin):
                messages.error(request, 'Solo se permiten horas en punto, por ejemplo 08:00 o 16:00.')
                return redirect('admin_panel')

            horario.hora_inicio = hora_inicio
            horario.hora_fin = hora_fin
            horario.save(update_fields=['hora_inicio', 'hora_fin'])
            messages.success(request, 'Horario actualizado correctamente.')
            return redirect('admin_panel')

        if action == 'delete_horario':
            horario_id = request.POST.get('horario_id')
            horario = get_object_or_404(HorarioAtencion, id=horario_id)
            horario.delete()
            messages.success(request, 'Día eliminado del horario del médico.')
            return redirect('admin_panel')

        if action == 'update_recepcionista':
            recep_id = request.POST.get('recepcionista_id')
            nombre = (request.POST.get('nombre') or '').strip()
            correo = (request.POST.get('correo') or '').strip()
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''

            if not recep_id:
                messages.error(request, 'Recepcionista no válido.')
                return redirect('admin_panel')

            recep_user = get_object_or_404(User, id=recep_id)

            if not nombre or not correo or not username:
                messages.error(request, 'Debe completar nombre, correo y usuario del recepcionista.')
                return redirect('admin_panel')

            # Verificar cambio de username
            if User.objects.filter(username=username).exclude(id=recep_user.id).exists():
                messages.error(request, 'El nombre de usuario ya está en uso por otro usuario.')
                return redirect('admin_panel')

            nombres = nombre.split(' ', 1)
            recep_user.first_name = nombres[0]
            recep_user.last_name = nombres[1] if len(nombres) > 1 else ''
            recep_user.email = correo
            recep_user.username = username

            if password:
                if len(password) < 6:
                    messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
                    return redirect('admin_panel')
                recep_user.set_password(password)

            recep_user.save()
            messages.success(request, 'Recepcionista actualizado correctamente.')
            return redirect('admin_panel')

        if action == 'delete_recepcionista':
            recep_id = request.POST.get('recepcionista_id')

            if not recep_id:
                messages.error(request, 'Recepcionista no válido.')
                return redirect('admin_panel')

            recep_user = get_object_or_404(User, id=recep_id)
            recep_user.delete()
            messages.success(request, 'Recepcionista eliminado correctamente.')
            return redirect('admin_panel')

        messages.error(request, 'Acción no válida.')
        return redirect('admin_panel')
    
    total_medicos = Doctor.objects.count()
    total_pacientes = Paciente.objects.count()
    citas_programadas = Cita.objects.filter(estado='programada').count()
    
    medicos = Doctor.objects.filter(activo=True).prefetch_related('horarios')

    recep_group, _ = Group.objects.get_or_create(name='Recepcionista')
    recepcionistas = recep_group.user_set.all().order_by('first_name', 'last_name', 'username')
    
    context = {
        'total_medicos': total_medicos,
        'total_pacientes': total_pacientes,
        'citas_programadas': citas_programadas,
        'medicos': medicos,
        'recepcionistas': recepcionistas,
    }
    
    return render(request, 'citas/admin_panel.html', context)


def mis_citas(request):
    """Mis citas (paciente)"""
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('index')
    
    paciente = get_object_or_404(Paciente, id=paciente_id)
    citas = paciente.citas.all().order_by('-fecha', '-hora')
    
    context = {
        'paciente': paciente,
        'citas': citas,
    }
    
    return render(request, 'citas/mis_citas.html', context)


@require_http_methods(["POST"])
def obtener_horas_disponibles(request):
    """API para obtener horas disponibles (AJAX)"""
    doctor_id = request.POST.get('doctor_id')
    fecha_str = request.POST.get('fecha')
    
    if not doctor_id or not fecha_str:
        return JsonResponse({'error': 'Datos incompletos'}, status=400)
    
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        if fecha < datetime.now().date():
            return JsonResponse({'horas': []})

        dia_semana = fecha.weekday()
        
        horarios = doctor.horarios.filter(dia_semana=dia_semana)
        
        if not horarios.exists():
            return JsonResponse({'horas': []})
        
        horas = generar_horas_disponibles(doctor, fecha, horarios.first())
        return JsonResponse({'horas': horas})
    
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)


@require_http_methods(["POST"])
def buscar_doctores(request):
    """API para buscar doctores (AJAX) - Filtra según edad del paciente"""
    nombre = (request.POST.get('nombre') or '').strip()
    paciente_id = request.POST.get('paciente_id')
    
    if not nombre:
        return JsonResponse({'error': 'Nombre requerido'}, status=400)
    
    # Buscar doctores por nombre
    doctores = Doctor.objects.filter(
        nombre__icontains=nombre,
        activo=True
    )
    
    # Si hay paciente, filtrar según su edad
    if paciente_id:
        try:
            paciente = Paciente.objects.get(id=paciente_id)
            if paciente.es_menor_de_edad():
                doctores = doctores.filter(especialidad='pediatria')
        except Paciente.DoesNotExist:
            pass
    
    resultado = [{
        'id': doctor.id,
        'nombre': doctor.nombre,
        'especialidad': doctor.get_especialidad_display(),
    } for doctor in doctores]
    
    return JsonResponse({'doctores': resultado})


@require_http_methods(["POST"])
def buscar_pacientes(request):
    """API para buscar pacientes (AJAX) - Por cédula o nombre"""
    query = (request.POST.get('query') or '').strip()
    
    if not query:
        return JsonResponse({'error': 'Búsqueda requerida'}, status=400)
    
    # Buscar pacientes por cédula o nombre
    pacientes = Paciente.objects.filter(
        Q(documento_identidad__icontains=query) |
        Q(nombre_completo__icontains=query)
    ).order_by('nombre_completo')[:20]  # Limitar a 20 resultados
    
    resultado = [{
        'id': paciente.id,
        'nombre': paciente.nombre_completo,
        'documento': paciente.documento_identidad,
        'telefono': paciente.telefono,
        'es_menor': paciente.es_menor_de_edad(),
    } for paciente in pacientes]
    
    return JsonResponse({'pacientes': resultado})


@login_required
@require_http_methods(["GET", "POST"])
def editar_cita(request, cita_id):
    """Editar fecha, hora y doctor de una cita existente"""
    user = request.user
    if not user.groups.filter(name='Recepcionista').exists():
        return redirect('index')
    
    cita = get_object_or_404(Cita, id=cita_id)
    
    if request.method == 'POST':
        # Actualizar fecha, hora y doctor
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        doctor_id = request.POST.get('doctor_id')
        
        # Validar fecha
        if not fecha_str:
            return JsonResponse({'error': 'Debe proporcionar una fecha.'}, status=400)
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            if fecha < datetime.now().date():
                return JsonResponse({'error': 'No se pueden agendar citas en fechas pasadas.'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Fecha inválida.'}, status=400)
        
        # Validar hora
        if not hora_str:
            return JsonResponse({'error': 'Debe proporcionar una hora.'}, status=400)
        
        try:
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Hora inválida.'}, status=400)

        if not es_hora_futura(fecha, hora):
            return JsonResponse({'error': 'Solo se pueden programar horas futuras para el día de hoy.'}, status=400)
        
        # Si se proporciona doctor_id, usar ese; si no, mantener el actual
        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id, activo=True)
            except Doctor.DoesNotExist:
                return JsonResponse({'error': 'Doctor no válido.'}, status=400)
        else:
            doctor = cita.doctor
        
        # Verificar que la hora no esté ocupada en la nueva fecha/doctor
        hora_conflicto = Cita.objects.filter(
            doctor=doctor,
            fecha=fecha,
            hora=hora
        ).exclude(id=cita.id).exists()
        
        if hora_conflicto:
            return JsonResponse({'error': 'El doctor ya tiene una cita en esa hora y fecha.'}, status=400)
        
        # Actualizar la cita
        cita.fecha = fecha
        cita.hora = hora
        cita.doctor = doctor
        cita.save()
        
        messages.success(request, 'Cita actualizada correctamente.')
        return JsonResponse({'success': True})
    
    # GET: Retornar datos de la cita en JSON para cargar en el modal
    context = {
        'id': cita.id,
        'paciente': cita.paciente.nombre_completo,
        'doctor': cita.doctor.nombre,
        'doctor_id': cita.doctor.id,
        'fecha': cita.fecha.strftime('%Y-%m-%d'),
        'hora': cita.hora.strftime('%H:%M'),
    }
    return JsonResponse(context)


@login_required
@require_http_methods(["POST"])
def eliminar_cita(request, cita_id):
    """Eliminar una cita"""
    user = request.user
    if not user.groups.filter(name='Recepcionista').exists():
        return JsonResponse({'error': 'No tienes permiso para eliminar citas.'}, status=403)
    
    cita = get_object_or_404(Cita, id=cita_id)
    
    try:
        cita.delete()
        messages.success(request, 'Cita eliminada correctamente.')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': 'Error al eliminar la cita.'}, status=500)
