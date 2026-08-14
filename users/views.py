from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdministrateur
from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AuditLogSerializer,
)
from .audit_models import AuditLog
from notifications.services.notification_service import NotificationService

User = get_user_model()


# ============================================================
# AUTH : Register + Profile (existant, conservé tel quel)
# ============================================================

class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer

    permission_classes = [
        AllowAny
    ]


class ProfileView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


# ============================================================
# ADMIN : Gestion des utilisateurs
# ============================================================

class AdminUserListView(generics.ListAPIView):
    """
    GET /api/auth/admin/users/
    Recherche et liste des utilisateurs (ADMIN uniquement).
    Filtres: ?search=email_ou_nom&role=APPRENANT
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdministrateur]

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role.upper())

        return qs


class AdminUserDetailView(APIView):
    """
    GET /api/auth/admin/users/<id>/
    Consulte le profil complet d'un utilisateur.

    PATCH /api/auth/admin/users/<id>/
    Modifie le rôle, les quotas ou le statut d'un utilisateur.
    Journalise chaque modification dans AuditLog.
    Notifie l'utilisateur concerné.
    """
    permission_classes = [IsAuthenticated, IsAdministrateur]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        changes = []
        for field, new_value in serializer.validated_data.items():
            old_value = getattr(target_user, field)

            if str(old_value) != str(new_value):
                # Journaliser
                AuditLog.objects.create(
                    author=request.user,
                    target_user=target_user,
                    action=f"Modification de {field}",
                    field_name=field,
                    old_value=str(old_value),
                    new_value=str(new_value),
                )
                setattr(target_user, field, new_value)
                changes.append(f"{field}: {old_value} → {new_value}")

        if changes:
            target_user.save()
            # Notifier l'utilisateur
            NotificationService.create(
                user=target_user,
                notification_type="ADMIN_ACTION",
                title="Modification de votre compte",
                message="Un administrateur a modifié votre compte : " + " | ".join(changes),
                metadata={"modified_by": request.user.email, "changes": changes}
            )

        return Response({
            "detail": f"{len(changes)} modification(s) appliquée(s).",
            "changes": changes,
            "user": AdminUserSerializer(target_user).data,
        })


class AuditLogListView(generics.ListAPIView):
    """
    GET /api/auth/admin/audit-log/
    Historique des modifications administratives.
    Filtre: ?user_id=<id>
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdministrateur]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(target_user_id=user_id)
        return qs