
Aplicación web desarrollada con Django para la gestión de citas médicas. Permite a recepcionistas agendar citas, doctores ver su agenda y pacientes consultar sus próximas citas.
Características

Gestión de Citas
- Agendar citas de 30 minutos
- Seleccionar fecha para ver disponibilidad del médico
- Consultar citas por paciente
- Estados de cita: Programada, Confirmada, Realizada, Cancelada

Panel de Recepción
- Registrar nuevos pacientes
- Buscar pacientes y sus citas
- Agendar citas (búsqueda de paciente por cédula, búsqueda de doctor por nombre)
- Dashboard con estadísticas

Calendario Médico
- Vista de agenda por fecha
- Mostrar horarios de atención
- Listar citas programadas para el día
- Citas de 30 minutos

Panel de Administración
- Gestionar médicos y sus especialidades
- Configurar horarios de atención por día
- Ver estadísticas del sistema

Portal del Paciente
- Consultar próximas citas
- Ver información de médicos y especialidades
- Interfaz intuitiva


Modelos de Datos

Paciente
- Nombre completo
- Documento de identidad (único)
- Teléfono
- Correo electrónico
- Fecha de creación

Doctor
- Nombre
- Especialidad (Medicina General, Pediatría, etc.)
- Usuario (login)
- Estado (Activo/Inactivo)
- Relación con User (Django)

HorarioAtencion
- Doctor (FK)
- Día de la semana
- Hora inicio
- Hora fin

Cita
- Paciente (FK)
- Doctor (FK)
- Fecha
- Hora
- Estado (Programada, Confirmada, Realizada, Cancelada)
- Notas opcionales


