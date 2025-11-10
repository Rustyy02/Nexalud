from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Solo administradores pueden acceder.
    """
    def has_permission(self, request, view):
        # Debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Debe ser staff o superuser
        return request.user.is_staff or request.user.is_superuser


class IsSuperUser(permissions.BasePermission):
    """
    Permiso estricto: Solo superusuarios.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )