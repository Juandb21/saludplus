# -*- coding: utf-8 -*-
"""
Script para cargar datos de ejemplo en la base de datos
Ejecutar con: python manage.py shell < citas/load_data.py
"""

from django.contrib.auth.models import User, Group
from citas.models import Doctor, Paciente, HorarioAtencion, Cita
from datetime import time, date, timedelta

print("Creando grupos de usuarios...")

# Crear grupos
groups = ['Recepcionista', 'Doctor', 'Administrador']
for group_name in groups:
    group, created = Group.objects.get_or_create(name=group_name)
    if created:
        print(f"  - Grupo '{group_name}' creado")
    else:
        print(f"  - Grupo '{group_name}' ya existe")

print("\nCreando usuarios...")

# Crear usuario Recepcionista
try:
    user_recepcionista = User.objects.create_user(
        username='maria.garcia',
        password='recepcion123',
        first_name='María',
        last_name='García',
        email='maria@saludplus.com'
    )
    recepcionista_group = Group.objects.get(name='Recepcionista')
    user_recepcionista.groups.add(recepcionista_group)
    print("  - Usuario Recepcionista 'maria.garcia' creado")
except:
    print("  - Usuario Recepcionista 'maria.garcia' ya existe")

# Crear usuario Administrador
try:
    user_admin = User.objects.create_user(
        username='admin',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema',
        email='admin@saludplus.com'
    )
    admin_group = Group.objects.get(name='Administrador')
    user_admin.groups.add(admin_group)
    print("  - Usuario Administrador 'admin' creado")
except:
    print("  - Usuario Administrador 'admin' ya existe")

print("\nCreando doctores...")

# Crear doctores
try:
    doctor1 = Doctor.objects.create(
        nombre='Carlos López',
        especialidad='medicina_general',
        activo=True
    )
    user_doctor1 = User.objects.create_user(
        username='carlos.lopez',
        password='doctor123',
        first_name='Carlos',
        last_name='López',
        email='carlos@saludplus.com'
    )
    doctor1.usuario = user_doctor1
    doctor1.save()
    doctor_group = Group.objects.get(name='Doctor')
    user_doctor1.groups.add(doctor_group)
    print(f"  - Doctor 'Carlos López' creado")
except:
    doctor1 = Doctor.objects.get(nombre='Carlos López')
    print(f"  - Doctor 'Carlos López' ya existe")

try:
    doctor2 = Doctor.objects.create(
        nombre='María Rodríguez',
        especialidad='pediatria',
        activo=True
    )
    user_doctor2 = User.objects.create_user(
        username='maria.rodriguez',
        password='doctor123',
        first_name='María',
        last_name='Rodríguez',
        email='maria.rodriguez@saludplus.com'
    )
    doctor2.usuario = user_doctor2
    doctor2.save()
    user_doctor2.groups.add(doctor_group)
    print(f"  - Doctor 'María Rodríguez' creado")
except:
    doctor2 = Doctor.objects.get(nombre='María Rodríguez')
    print(f"  - Doctor 'María Rodríguez' ya existe")

print("\nCreando horarios de atención...")

# Horarios para Dr. Carlos López
try:
    # Lunes a Viernes 08:00 - 12:00
    for dia in range(5):  # 0=Lunes, 4=Viernes
        HorarioAtencion.objects.get_or_create(
            doctor=doctor1,
            dia_semana=dia,
            defaults={'hora_inicio': time(8, 0), 'hora_fin': time(12, 0)}
        )
    
    # Lunes, Miércoles, Viernes 14:00 - 18:00
    for dia in [0, 2, 4]:
        HorarioAtencion.objects.get_or_create(
            doctor=doctor1,
            dia_semana=dia,
            defaults={'hora_inicio': time(14, 0), 'hora_fin': time(18, 0)}
        )
    print("  - Horarios de Dr. Carlos López configurados")
except Exception as e:
    print(f"  - Error configurando horarios de Dr. Carlos López: {e}")

# Horarios para Dra. María Rodríguez
try:
    # Martes, Jueves 09:00 - 12:00
    for dia in [1, 3]:
        HorarioAtencion.objects.get_or_create(
            doctor=doctor2,
            dia_semana=dia,
            defaults={'hora_inicio': time(9, 0), 'hora_fin': time(12, 0)}
        )
    
    # Martes, Jueves 14:00 - 17:00
    for dia in [1, 3]:
        HorarioAtencion.objects.get_or_create(
            doctor=doctor2,
            dia_semana=dia,
            defaults={'hora_inicio': time(14, 0), 'hora_fin': time(17, 0)}
        )
    print("  - Horarios de Dra. María Rodríguez configurados")
except Exception as e:
    print(f"  - Error configurando horarios de Dra. María Rodríguez: {e}")

print("\nCreando pacientes...")

# Crear pacientes
try:
    paciente1 = Paciente.objects.create(
        nombre_completo='Juan Pérez',
        documento_identidad='12345678',
        telefono='555-0001',
        correo='juan.perez@email.com'
    )
    print("  - Paciente 'Juan Pérez' creado")
except:
    print("  - Paciente 'Juan Pérez' ya existe")
    paciente1 = Paciente.objects.get(documento_identidad='12345678')

try:
    paciente2 = Paciente.objects.create(
        nombre_completo='Ana Martínez',
        documento_identidad='87654321',
        telefono='555-0002',
        correo='ana.martinez@email.com'
    )
    print("  - Paciente 'Ana Martínez' creado")
except:
    print("  - Paciente 'Ana Martínez' ya existe")
    paciente2 = Paciente.objects.get(documento_identidad='87654321')

print("\nCreando citas de ejemplo...")

# Crear citas
try:
    cita1 = Cita.objects.create(
        paciente=paciente1,
        doctor=doctor1,
        fecha=date.today() + timedelta(days=1),
        hora=time(9, 0),
        estado='programada'
    )
    print("  - Cita 1 creada")
except Exception as e:
    print(f"  - Cita 1 ya existe o error: {e}")

try:
    cita2 = Cita.objects.create(
        paciente=paciente2,
        doctor=doctor2,
        fecha=date.today() + timedelta(days=2),
        hora=time(10, 0),
        estado='programada'
    )
    print("  - Cita 2 creada")
except Exception as e:
    print(f"  - Cita 2 ya existe o error: {e}")

print("\n✓ Datos de ejemplo cargados exitosamente")
print("\nCredenciales para pruebas:")
print("  Recepcionista: maria.garcia / recepcion123")
print("  Doctor 1: carlos.lopez / doctor123")
print("  Doctor 2: maria.rodriguez / doctor123")
print("  Administrador: admin / admin123")
print("  Paciente 1: 12345678")
print("  Paciente 2: 87654321")
