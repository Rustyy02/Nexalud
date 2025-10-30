# 🏗️ Arquitectura del Sistema - Nexalud

<div align="center">

[🏠 Inicio](README.md) | 
[👈 Anterior: Instalación](INSTALLATION.md) | 

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
    USUARIO ||--o{ ATENCION : "gestiona"
    
    PACIENTE {
        uuid id PK
        string rut UK
        string nombre
        string apellido_paterno
        string apellido_materno
        string estado_actual
        string etapa_actual
        json metadatos_adicionales
        datetime fecha_ingreso
    }
    
    ATENCION {
        uuid id PK
        uuid paciente_id FK
        uuid medico_id FK
        uuid box_id FK
        datetime fecha_hora_inicio
        datetime fecha_hora_fin
        integer duracion_planificada
        integer duracion_real
        string estado
        string tipo_atencion
        datetime inicio_cronometro
        datetime fin_cronometro
    }
    
    RUTA_CLINICA {
        uuid id PK
        uuid paciente_id FK
        json etapas_seleccionadas
        string etapa_actual
        float porcentaje_completado
        string estado
        json timestamps_etapas
    }
    
    MEDICO {
        uuid id PK
        string codigo_medico UK
        string nombre
        string apellido
        string especialidad_principal
        json especialidades_secundarias
    }
    
    BOX {
        uuid id PK
        string numero UK
        string nombre
        string especialidad
        string estado
        integer capacidad_maxima
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

## Diagrama de Secuencia - Dashboard

```mermaid
sequenceDiagram
    participant F as Frontend
    participant D as API Dashboard
    participant A as API Atenciones
    participant P as API Pacientes
    participant B as API Boxes

    Note over F: Cada 30 segundos
    F->>D: GET /api/dashboard/metricas/
    D->>A: Consultar atenciones hoy
    A->>A: Contar atenciones
    D->>P: Consultar pacientes activos
    P->>P: Contar por estado
    D->>B: Consultar boxes
    B->>B: Calcular ocupación
    D->>F: Métricas consolidadas
    F->>F: Actualizar componentes
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
```

# Decisiones técnicas

## ¿Por qué Django REST Framework?

- Rápido desarrollo -> APIs -> CRUD en minutos con ModelViewSet
- Serializers robustos -> Validación compleja de datos médicos
- Autenticación integrada -> JWT + permisos por rol
- Documentación automática -> Swagger/OpenAPI integrado
- Comunidad activa -> Soluciones probadas y mantenidas

## ¿Por qué React + Material-UI?

- Componentes reutilizables -> Formularios médicos consistentes
- Ecosistema rico -> Gráficos, tablas, formularios
- Performance -> Virtual DOM para interfaces complejas
- Developer Experience -> Hot reload, herramientas de debugging

## ¿Por qué SQLite para Desarrollo?

- Velocidad de desarrollo -> Sin configuración de base de datos
- Portabilidad -> Todo el equipo usa misma configuración
- Testing -> Bases de datos en memoria para tests
- Migración futura -> Mismo ORM para SQLite y PostgreSQL

