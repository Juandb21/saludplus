# Guía de Despliegue en Render

## Pasos para desplegar SaludPlus en Render

### 1. Preparación Inicial

1. Asegúrate de tener todos los cambios confirmados en Git:
   ```bash
   git add .
   git commit -m "Configuración para despliegue en Render"
   ```

2. Push a tu repositorio (GitHub/GitLab):
   ```bash
   git push origin main
   ```

### 2. En Render.com

1. Crea una cuenta en [Render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Selecciona "New +" > "Web Service"

### 3. Configuración del Servicio Web

- **Name**: `saludplus`
- **Repository**: Selecciona tu repositorio
- **Branch**: `main` (o la rama que uses)
- **Runtime**: `Python 3`
- **Build Command**: `bash build.sh`
- **Start Command**: `gunicorn saludplus.wsgi:application`

### 4. Configuración de Variables de Entorno

En la sección "Environment Variables", agrega:

```
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=false
DATABASE_URL=postgresql://...  (se configura automáticamente con la BD)
ALLOWED_HOSTS=tu-dominio.onrender.com,www.tu-dominio.onrender.com
```

### 5. Crear Base de Datos PostgreSQL

1. En Render, ve a "Databases"
2. Crea una nueva base de datos PostgreSQL:
   - **Name**: `saludplus-db`
   - **Region**: Elige la misma que tu web service
   - **PostgreSQL Version**: 15 o superior

3. La `DATABASE_URL` se agregará automáticamente

### 6. Desplegar Automáticamente

Una vez configurado, cada vez que hagas push a `main`, Render desplegará automáticamente.

## Variables de Entorno Importantes

- **SECRET_KEY**: Clave secreta (Render puede generarla automáticamente)
- **DEBUG**: Debe ser `false` en producción
- **DATABASE_URL**: URL de la base de datos PostgreSQL
- **ALLOWED_HOSTS**: Dominio de tu aplicación

## Verificación Post-Despliegue

1. Accede a tu aplicación en la URL que Render proporciona
2. Verifica los logs en el panel de Render
3. Prueba el login y funcionalidades principales

## Solución de Problemas

- Si hay errores en migraciones, ejecuta:
  ```bash
  python manage.py migrate
  ```
- Si los archivos estáticos no se cargan:
  ```bash
  python manage.py collectstatic --noinput
  ```

## Costos

- Web Service gratuito (con límites)
- Base de datos PostgreSQL gratuita (limitada)
- Dominio personalizado requiere plan pagado

¡Tu aplicación estará lista para producción!
