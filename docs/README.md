# 🏥 Nexalud - Sistema de apoyo a la Gestión Hospitalaria

![Django](https://img.shields.io/badge/Django-5.2.6-green)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

Sistema integral para la gestión de pacientes, atenciones médicas y flujos clínicos.

## ✨ Características

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| 🏥 Pacientes | ✅ Completado | Gestión completa con validación RUT |
| ⏱️ Atenciones | ✅ Completado | Sistema con cronómetro integrado |
| 📊 Dashboard | 🚧 Desarrollo | Métricas en tiempo real |
| 🚦 Rutas Clínicas | ✅ Completado | Flujos clínicos automatizados |

## 🚀 Comenzando Rápido

### Prerrequisitos
- Python 3.10+
- Node.js 16+
- SQLite

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/Rustyy02/nexalud.git
cd nexalud

# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (otra terminal)
cd frontend
npm install
npm start
```

## Documentación

- [📖 Guía de Instalación Completa](INSTALLATION.md)
- [🏗️ Arquitectura](ARCHITECTURE.md)

## Estructura del Proyecto

nexalud/

├── backend/          # Django REST API

├── frontend/         # React Application

├── docs/            # Documentación

└── docker-compose.yml

## Tecnologías
- Backend: Django, Django REST Framework, SQLite
- Frontend: React, Material-UI, Axios
- Herramientas: Docker, Git, GitHub Actions
