# 📖 Guía de Instalación - Nexalud

<div align="center">

[🏠 Inicio](README.md) | 
[👈 Anterior: Arquitectura](ARCHITECTURE.md) | 

</div>

## 🛠️ Requisitos del Sistema

### Software Requerido
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 16+](https://nodejs.org/)
- [SQLite] (Incluido con Python)
- [Git](https://git-scm.com/)

### Verificar Instalaciones
```bash
# Verificar Python
python --version
# Python 3.10.0

# Verificar Node.js
node --version
# v16.14.0

# Verificar PostgreSQL
psql --version
# psql (PostgreSQL) 13.4
```

## 🏗️ Instalación Manual
1. Clonar Repositorio

```bash
git clone https://github.com/tuusuario/nexalud.git
cd nexalud
```

2. Configurar Backend
```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# ⚡ CON SQLITE: No se necesitan variables de entorno especiales

# La base de datos se crea automáticamente en db.sqlite3

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
``