from rest_framework.permissions import BasePermission


class IsAdministrateur(BasePermission):
    """
    Autorise uniquement les utilisateurs ayant le rôle ADMINISTRATEUR.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMINISTRATEUR"
        )


class IsOwner(BasePermission):
    """
    Autorise uniquement le propriétaire de la ressource.
    L'objet doit posséder un attribut 'user' ou 'uploaded_by'.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
