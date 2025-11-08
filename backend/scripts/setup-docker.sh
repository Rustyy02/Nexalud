#!/bin/bash

echo "🚀 Configurando Django en Docker..."

# Esperar a que la base de datos esté lista
sleep 5

# Ejecutar migraciones
echo "📦 Aplicando migraciones..."
python manage.py migrate

# Crear superusuario si no existe
echo "👤 Creando superusuario..."
if [ -z "$(python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='admin').exists())" 2>/dev/null)" ]; then
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@nexalud.com', 'admin123')" | python manage.py shell
    echo "✅ Superusuario creado: admin / admin123"
else
    echo "✅ Superusuario ya existe"
fi

echo "🎉 Configuración completada!"