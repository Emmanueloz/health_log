# Microservices Monorepo

This is a monorepo containing three microservices:

1. Authentication Service
2. Business Logic Service
3. Notification Service

## Project Structure

```
├── .env.example
├── docker-compose.yml
├── README.md
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── auth_routes.py
│   │   └── utils/
│   │       └── __init__.py
│   └── config.py
├── business-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── business_routes.py
│   │   └── utils/
│   │       └── __init__.py
│   └── config.py
└── notification-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── __init__.py
    │   ├── services/
    │   │   └── email_service.py
    │   ├── routes/
    │   │   ├── __init__.py
    │   │   └── notification_routes.py
    │   └── utils/
    │       └── __init__.py
    └── config.py
```

## Getting Started

1. Copy `.env.example` to `.env` and update the environment variables
2. Run `docker compose up --build` to start all services
3. Access the services on their respective ports:
   - Auth Service: http://localhost:5000
   - Business Service: http://localhost:5001
   - Notification Service: http://localhost:5002

## Services

### Auth Service

Handles user authentication and authorization.

### Business Service

Contains the main business logic of the application.

### Notification Service

Handles sending notifications (emails, etc.)

## Development

Each service has its own Dockerfile and requirements.txt for dependencies. The services communicate with each other via HTTP requests.

### 1️⃣ Construir la Imagen

```bash
docker build -f Dockerfile -t health-log-monolith:latest .
```

**Tiempo estimado**: 5-10 minutos (primera vez)

### 2️⃣ Ejecutar el Contenedor

```bash
docker run -d \
    -p 5000:5000 \
    -p 5001:5001 \
    -p 5002:5002 \
    --name health-log-app \
    health-log-monolith:latest
```

### 3️⃣ Verificar que Funciona

```bash
# Ver logs
docker logs -f health-log-app

# Verificar servicios
docker exec health-log-app supervisorctl status
```

## 📍 Acceso a los Servicios

- **Auth Service**: http://localhost:5000
- **Business Service**: http://localhost:5001
- **Notification Service**: http://localhost:5002

## 🛠️ Comandos Útiles

```bash
# Detener
docker stop health-log-app

# Iniciar
docker start health-log-app

# Reiniciar
docker restart health-log-app

# Ver logs en tiempo real
docker logs -f health-log-app

# Eliminar
docker stop health-log-app && docker rm health-log-app
```

## ⚠️ Notas Importantes

1. **Primera ejecución**: Los servicios pueden tardar 30-60 segundos en estar completamente listos
2. **Puertos**: Asegúrate de que los puertos 5000, 5001 y 5002 estén disponibles
3. **Recursos**: La imagen requiere aproximadamente 1-2 GB de espacio en disco
4. **Datos**: Los datos NO persisten cuando eliminas el contenedor

## 🔍 Solución Rápida de Problemas

### El contenedor no inicia

```bash
docker logs health-log-app
```

### Un servicio no responde

```bash
docker exec health-log-app supervisorctl status
docker exec health-log-app supervisorctl restart <nombre-servicio>
```

### Reiniciar todo

```bash
docker restart health-log-app
```
