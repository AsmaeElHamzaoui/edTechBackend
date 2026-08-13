import logging

logger = logging.getLogger(__name__)


class NotificationAgent:
    """
    Agent de notification : déclenchement des notifications in-app et email.
    Centralise toutes les alertes de la plateforme.
    """

    @staticmethod
    def notify_document_ready(document):
        """Notifie l'utilisateur que son document est prêt."""
        try:
            from notifications.services.notification_service import NotificationService
            NotificationService.create(
                user=document.uploaded_by,
                notification_type="DOCUMENT_READY",
                title="Document prêt",
                message=f"Votre document « {document.title} » a été traité et est maintenant disponible.",
                metadata={"document_id": document.id}
            )
        except Exception as e:
            logger.error(f"NotificationAgent: failed to notify document_ready: {e}")

    @staticmethod
    def notify_document_failed(document):
        """Notifie l'utilisateur qu'un document a échoué."""
        try:
            from notifications.services.notification_service import NotificationService
            NotificationService.create(
                user=document.uploaded_by,
                notification_type="DOCUMENT_FAILED",
                title="Échec du traitement",
                message=f"Le traitement de votre document « {document.title} » a échoué : {document.error_message}",
                metadata={"document_id": document.id}
            )
        except Exception as e:
            logger.error(f"NotificationAgent: failed to notify document_failed: {e}")

    @staticmethod
    def notify_quiz_result(user, quiz, score):
        """Notifie l'utilisateur de son résultat de quiz."""
        try:
            from notifications.services.notification_service import NotificationService
            NotificationService.create(
                user=user,
                notification_type="QUIZ_RESULT",
                title="Résultat de quiz",
                message=f"Vous avez obtenu {score:.1f}% au quiz « {quiz.title} ».",
                metadata={"quiz_id": quiz.id, "score": score}
            )
        except Exception as e:
            logger.error(f"NotificationAgent: failed to notify quiz_result: {e}")

    @staticmethod
    def execute(user, notification_type: str, context: dict = None) -> dict:
        """Point d'entrée générique depuis l'orchestrateur."""
        logger.info(f"NotificationAgent triggered: {notification_type} for user {user.id}")
        return {
            "agent": "NotificationAgent",
            "intent": "NOTIFY",
            "data": {
                "status": "dispatched",
                "type": notification_type,
            }
        }
