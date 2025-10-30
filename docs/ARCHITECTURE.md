# 🏗️ Arquitectura del Sistema - Nexalud

<div align="center">

[🏠 Inicio](README.md) | 
[👈 Anterior: Instalación](installation.md) | 

</div>

## 📋 Tabla de Contenidos

- [📐 Visión General](#visión-general)
- [🏛️ Patrón Arquitectónico](#patrón-arquitectónico)
- [🗄️ Capa de Datos](#capa-de-datos)

# 📐 Visión General

Nexalud es un sistema de gestión hospitalaria construido con **Django REST Framework** en el backend y **React** en el frontend, utilizando **SQLite** para desarrollo y pruebas.

## Diagrama de Arquitectura

```mermaid
graph TB
    A[👨‍💼 Usuario] --> B[🌐 Frontend React]
    B --> C[🔄 API REST Django]
    
    C --> D[🗄️ SQLite Database]
    C --> E[🔐 Authentication]
    C --> F[📊 Business Logic]
    
    subgraph "Backend Django"
        C
        E
        F
    end
    
    subgraph "Capa de Datos"
        D
    end
    
    D --> G[📁 db.sqlite3]
    
    style B fill:#cde4ff
    style C fill:#ffd8cc
    style D fill:#e4ffcd
```

# 🏛️ Patrón Arquitectónico

Arquitectura en Capas

📁 Nexalud/

├── 🎨 Frontend (Presentación)

│   └── React SPA + Material-UI

├── 🔄 Backend (Lógica de Negocio)

│   └── Django REST API

├── 🗄️ Persistencia (Datos)

│   └── SQLite + Django ORM

└── 🔐 Seguridad

    └── JWT + CORS + Permisos


## Principios de Diseño

- Separación de Concerns: Frontend y backend completamente independientes
- API-First: Backend como servicio reusable
- Stateless: Autenticación JWT sin estado
- RESTful: APIs siguiendo convenciones REST

# 🗄️ Capa de Datos

Base de Datos - SQLite (Desarrollo)

Configuración Actual:
python

```bash
# backend/config/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Archivo único
    }
}
```

## Ventajas para Desarrollo:

- Configuración cero: No requiere servidor externo
- Portable: Todo en un archivo, fácil de versionar
- Rápido: Ideal para desarrollo y pruebas
- Compatibilidad: Mismo ORM que PostgreSQL

## Diagrama de Entidad Relacional

```mermaid
erDiagram
    PACIENTE ||--o{ ATENCION : "tiene"
    PACIENTE ||--o{ RUTA_CLINICA : "sigue"
    MEDICO ||--o{ ATENCION : "realiza"
    BOX ||--o{ ATENCION : "utiliza"
    
    PACIENTE {
        uuid id PK
        string rut UK
        string nombre
        string estado_actual
        string etapa_actual
    }
    
    ATENCION {
        uuid id PK
        uuid paciente_id FK
        uuid medico_id FK
        uuid box_id FK
        datetime fecha_hora_inicio
        string estado
    }
```

## Diagrama de Secuencia - Creacion atencion medica

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant A as API Atenciones
    participant P as API Pacientes
    participant B as API Boxes
    participant DB as Base de Datos

    U->>F: Crear nueva atención
    F->>A: POST /api/atenciones/
    A->>P: Verificar paciente
    P->>DB: Consultar paciente
    A->>B: Verificar box
    B->>DB: Consultar box
    A->>DB: Crear atención
    A->>F: 201 Created
    F->>U: Confirmación
```

## Diagrama de Secuencia - Sincronización de rutas clínicas

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant R as API Rutas
    participant P as API Pacientes
    participant DB as Base de Datos

    U->>F: Avanzar etapa
    F->>R: POST /rutas/{id}/avanzar/
    R->>P: PATCH /pacientes/{id}/
    P->>DB: Actualizar paciente
    R->>DB: Actualizar ruta
    R->>F: 200 OK
    F->>U: UI actualizada
```

## Diagrama de Capas

```mermaid
graph TB
    subgraph "Capa de Presentación"
        A[React SPA]
        B[Material-UI]
    end
    
    subgraph "Capa de Aplicación"
        C[Django REST API]
        D[Serializers]
        E[ViewSets]
    end
    
    subgraph "Capa de Dominio"
        F[Models]
        G[Business Logic]
    end
    
    subgraph "Capa de Persistencia"
        H[SQLite]
        I[Django ORM]
    end
    
    A --> C
    C --> F
    F --> H
    B --> A
    D --> C
    E --> C
    G --> F
    I --> H


