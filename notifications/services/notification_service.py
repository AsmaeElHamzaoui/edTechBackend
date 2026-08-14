import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from notifications.models import Notification, EmailLog

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def create(user, notification_type: str, title: str, message: str, metadata: dict = None) -> Notification:
        """Crée une notification in-app."""
        notif = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        logger.info(f"Notification created [{notification_type}] for user {user.email}")
        return notif

    @staticmethod
    def mark_as_read(notification_id: int, user) -> bool:
        """Marque une notification comme lue (avec vérification propriétaire)."""
        updated = Notification.objects.filter(
            id=notification_id,
            user=user
        ).update(status=Notification.Status.READ)
        return updated > 0

    @staticmethod
    def mark_all_as_read(user) -> int:
        """Marque toutes les notifications de l'utilisateur comme lues."""
        return Notification.objects.filter(
            user=user,
            status=Notification.Status.UNREAD
        ).update(status=Notification.Status.READ)

    @staticmethod
    def get_unread_count(user) -> int:
        return Notification.objects.filter(user=user, status=Notification.Status.UNREAD).count()
