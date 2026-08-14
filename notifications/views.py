from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Notification, EmailLog
from .serializers import NotificationSerializer, EmailLogSerializer
from .services.notification_service import NotificationService


class NotificationListView(ListAPIView):
    """
    GET /api/notifications/
    Liste les notifications de l'utilisateur connecté.
    Filtre optionnel : ?status=UNREAD
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs


class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/{id}/read/
    Marque une notification comme lue.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        success = NotificationService.mark_as_read(pk, request.user)
        if not success:
            return Response({"detail": "Notification introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Notification marquée comme lue."})


class NotificationMarkAllReadView(APIView):
    """
    POST /api/notifications/read-all/
    Marque toutes les notifications comme lues.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        return Response({"detail": f"{count} notifications marquées comme lues."})


class NotificationUnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Retourne le nombre de notifications non lues.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return Response({"unread_count": count})
