import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from notifications.models import EmailLog

logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def send(recipient: str, subject: str, body: str) -> EmailLog:
        """Envoie un email et enregistre le résultat dans EmailLog."""
        log = EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            body=body,
            status=EmailLog.Status.PENDING
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            log.status = EmailLog.Status.SENT
            log.sent_at = timezone.now()
            log.save(update_fields=["status", "sent_at"])
            logger.info(f"Email SENT to {recipient}: {subject}")

        except Exception as e:
            log.status = EmailLog.Status.FAILED
            log.error_message = str(e)
            log.save(update_fields=["status", "error_message"])
            logger.error(f"Email FAILED to {recipient}: {e}")

        return log

    @staticmethod
    def send_document_ready(user, document_title: str):
        EmailService.send(
            recipient=user.email,
            subject=f"[EdTech] Votre document « {document_title} » est prêt",
            body=(
                f"Bonjour {user.first_name},\n\n"
                f"Votre document « {document_title} » a été traité avec succès.\n"
                f"Vous pouvez maintenant le consulter, poser des questions ou générer un quiz.\n\n"
                f"Bonne révision !\nL'équipe EdTech"
            )
        )

    @staticmethod
    def send_document_failed(user, document_title: str, reason: str = ""):
        EmailService.send(
            recipient=user.email,
            subject=f"[EdTech] Échec du traitement de « {document_title} »",
            body=(
                f"Bonjour {user.first_name},\n\n"
                f"Le traitement de votre document « {document_title} » a échoué.\n"
                f"Cause : {reason or 'Erreur inconnue'}\n\n"
                f"Veuillez réessayer ou contacter le support.\n\nL'équipe EdTech"
            )
        )

    @staticmethod
    def send_quiz_result(user, quiz_title: str, score: float):
        EmailService.send(
            recipient=user.email,
            subject=f"[EdTech] Résultat de votre quiz « {quiz_title} »",
            body=(
                f"Bonjour {user.first_name},\n\n"
                f"Vous avez obtenu {score:.1f}% au quiz « {quiz_title} ».\n\n"
                f"Continuez ainsi !\nL'équipe EdTech"
            )
        )
