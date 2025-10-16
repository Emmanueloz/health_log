FROM ubuntu:22.04

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Mexico_City

# Establecer directorio de trabajo
WORKDIR /app

# Actualizar sistema e instalar dependencias base
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    postgresql-client \
    gcc \
    libpq-dev \
    supervisor \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Crear enlaces simbólicos para python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Actualizar pip
RUN pip3 install --upgrade pip

# Crear directorios para los microservicios
RUN mkdir -p /app/auth-service \
    /app/business-service \
    /app/notification-service \
    /var/log/supervisor \
    /var/log/postgresql \
    /var/run/postgresql

# Copiar requirements y código de cada servicio
COPY auth-service/requirements.txt /app/auth-service/
COPY business-service/requirements.txt /app/business-service/
COPY notification-service/requirements.txt /app/notification-service/

# Instalar dependencias de Python para todos los servicios
RUN pip3 install --no-cache-dir -r /app/auth-service/requirements.txt
RUN pip3 install --no-cache-dir -r /app/business-service/requirements.txt
RUN pip3 install --no-cache-dir -r /app/notification-service/requirements.txt

# Copiar el código de los servicios
COPY auth-service/ /app/auth-service/
COPY business-service/ /app/business-service/
COPY notification-service/ /app/notification-service/

# Configurar permisos para PostgreSQL
RUN chown -R postgres:postgres /var/lib/postgresql /var/log/postgresql /var/run/postgresql

# Configurar PostgreSQL
USER postgres

# Limpiar y reinicializar el cluster de PostgreSQL
RUN rm -rf /var/lib/postgresql/14/main && \
    mkdir -p /var/lib/postgresql/14/main && \
    /usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main

# Configurar PostgreSQL para aceptar conexiones
RUN echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/14/main/pg_hba.conf && \
    echo "listen_addresses='*'" >> /var/lib/postgresql/14/main/postgresql.conf

USER root

# Crear script de inicialización de bases de datos
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Iniciar PostgreSQL temporalmente\n\
su - postgres -c "/usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main -l /var/log/postgresql/postgresql.log start"\n\
\n\
# Esperar a que PostgreSQL esté listo\n\
sleep 5\n\
\n\
# Crear usuarios y bases de datos\n\
su - postgres -c "psql -c \\"CREATE USER auth_user WITH PASSWORD '\''auth_password'\'';\\""\n\
su - postgres -c "psql -c \\"CREATE DATABASE auth_db OWNER auth_user;\\""\n\
\n\
su - postgres -c "psql -c \\"CREATE USER business_user WITH PASSWORD '\''business_password'\'';\\""\n\
su - postgres -c "psql -c \\"CREATE DATABASE business_db OWNER business_user;\\""\n\
\n\
su - postgres -c "psql -c \\"CREATE USER notification_user WITH PASSWORD '\''notification_password'\'';\\""\n\
su - postgres -c "psql -c \\"CREATE DATABASE notification_db OWNER notification_user;\\""\n\
\n\
# Detener PostgreSQL\n\
su - postgres -c "/usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main stop"\n\
' > /usr/local/bin/init-databases.sh && chmod +x /usr/local/bin/init-databases.sh

# Ejecutar inicialización de bases de datos
RUN /usr/local/bin/init-databases.sh

# Crear configuración de Supervisor
RUN echo '[supervisord]\n\
nodaemon=true\n\
logfile=/var/log/supervisor/supervisord.log\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:postgresql]\n\
user=postgres\n\
command=/usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql/14/main\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/postgresql.err.log\n\
stdout_logfile=/var/log/supervisor/postgresql.out.log\n\
priority=1\n\
\n\
[program:auth-service]\n\
directory=/app/auth-service\n\
command=gunicorn --bind 0.0.0.0:5000 --workers 2 app:create_app()\n\
environment=FLASK_APP="app",FLASK_ENV="production",DATABASE_URL="postgresql://auth_user:auth_password@localhost:5432/auth_db",SECRET_KEY="your-secret-key-here-change-in-production"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/auth-service.err.log\n\
stdout_logfile=/var/log/supervisor/auth-service.out.log\n\
priority=10\n\
startsecs=10\n\
\n\
[program:business-service]\n\
directory=/app/business-service\n\
command=gunicorn --bind 0.0.0.0:5001 --workers 2 app:create_app()\n\
environment=FLASK_APP="app",FLASK_ENV="production",DATABASE_URL="postgresql://business_user:business_password@localhost:5432/business_db",AUTH_SERVICE_URL="http://localhost:5000",NOTIFICATION_SERVICE_URL="http://localhost:5002"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/business-service.err.log\n\
stdout_logfile=/var/log/supervisor/business-service.out.log\n\
priority=10\n\
startsecs=10\n\
\n\
[program:notification-service]\n\
directory=/app/notification-service\n\
command=gunicorn --bind 0.0.0.0:5002 --workers 2 app:create_app()\n\
environment=FLASK_APP="app",FLASK_ENV="production",DATABASE_URL="postgresql://notification_user:notification_password@localhost:5432/notification_db",SMTP_SERVER="smtp.example.com",SMTP_PORT="587",SMTP_USERNAME="your-email@example.com",SMTP_PASSWORD="your-email-password"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/notification-service.err.log\n\
stdout_logfile=/var/log/supervisor/notification-service.out.log\n\
priority=10\n\
startsecs=10\n\
' > /etc/supervisor/conf.d/supervisord.conf

# Crear script de inicio que ejecuta migraciones
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Iniciando PostgreSQL..."\n\
su - postgres -c "/usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main -l /var/log/postgresql/postgresql.log start"\n\
\n\
echo "Esperando a que PostgreSQL esté listo..."\n\
sleep 5\n\
\n\
# Ejecutar migraciones para cada servicio si existen\n\
echo "Ejecutando migraciones..."\n\
\n\
if [ -d "/app/auth-service/migrations" ]; then\n\
    cd /app/auth-service\n\
    export DATABASE_URL="postgresql://auth_user:auth_password@localhost:5432/auth_db"\n\
    flask db upgrade || echo "No hay migraciones para auth-service"\n\
fi\n\
\n\
if [ -d "/app/business-service/migrations" ]; then\n\
    cd /app/business-service\n\
    export DATABASE_URL="postgresql://business_user:business_password@localhost:5432/business_db"\n\
    flask db upgrade || echo "No hay migraciones para business-service"\n\
fi\n\
\n\
if [ -d "/app/notification-service/migrations" ]; then\n\
    cd /app/notification-service\n\
    export DATABASE_URL="postgresql://notification_user:notification_password@localhost:5432/notification_db"\n\
    flask db upgrade || echo "No hay migraciones para notification-service"\n\
fi\n\
\n\
echo "Deteniendo PostgreSQL temporal..."\n\
su - postgres -c "/usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main stop"\n\
\n\
echo "Iniciando todos los servicios con Supervisor..."\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf\n\
' > /usr/local/bin/start-services.sh && chmod +x /usr/local/bin/start-services.sh

# Exponer puertos de los servicios
EXPOSE 5000 5001 5002 5432

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando de inicio
CMD ["/usr/local/bin/start-services.sh"]
