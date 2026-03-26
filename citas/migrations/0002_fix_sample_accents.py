from django.db import migrations


def fix_sample_accents(apps, schema_editor):
    Doctor = apps.get_model('citas', 'Doctor')
    Paciente = apps.get_model('citas', 'Paciente')
    User = apps.get_model('auth', 'User')

    doctor_name_map = {
        'Carlos L??pez': 'Carlos López',
        'Mar??a Rodr??guez': 'María Rodríguez',
    }
    patient_name_map = {
        'Juan P??rez': 'Juan Pérez',
        'Ana Mart??nez': 'Ana Martínez',
    }
    first_name_map = {
        'Mar??a': 'María',
    }
    last_name_map = {
        'Garc??a': 'García',
        'L??pez': 'López',
        'Rodr??guez': 'Rodríguez',
    }

    for broken, fixed in doctor_name_map.items():
        Doctor.objects.filter(nombre=broken).update(nombre=fixed)

    for broken, fixed in patient_name_map.items():
        Paciente.objects.filter(nombre_completo=broken).update(nombre_completo=fixed)

    for broken, fixed in first_name_map.items():
        User.objects.filter(first_name=broken).update(first_name=fixed)

    for broken, fixed in last_name_map.items():
        User.objects.filter(last_name=broken).update(last_name=fixed)


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_sample_accents, migrations.RunPython.noop),
    ]
