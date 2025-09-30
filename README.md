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
