import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import timedelta

from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import LearningSession
from .serializers import LearningSessionSerializer
from documents.models import Document
from quiz.models import QuizAttempt, Answer, Question


def _parse_days(request, default=30):
    """Récupère le filtre de période depuis les query params."""
    try:
        return int(request.query_params.get("days", default))
    except (TypeError, ValueError):
        return default


class LearningSessionCreateView(CreateAPIView):
    """POST /api/analytics/sessions/ — Enregistre une session d'apprentissage."""
    serializer_class = LearningSessionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardView(APIView):
    """
    GET /api/analytics/dashboard/
    Tableau de bord complet : docs, quiz, temps, stockage.
    Filtres : ?days=30&document_id=<id>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request)
        since = timezone.now() - timedelta(days=days)

        doc_id = request.query_params.get("document_id")

        # ── Documents ──────────────────────────────────────────────────────
        docs_qs = Document.objects.filter(uploaded_by=user)
        if doc_id:
            docs_qs = docs_qs.filter(id=doc_id)

        documents_count  = docs_qs.count()
        documents_ready  = docs_qs.filter(status=Document.Status.READY).count()

        # ── Sessions d'apprentissage ───────────────────────────────────────
        sessions_qs = LearningSession.objects.filter(user=user, created_at__gte=since)
        if doc_id:
            sessions_qs = sessions_qs.filter(document_id=doc_id)

        total_time = sessions_qs.aggregate(total=Sum("duration_seconds"))["total"] or 0

        # ── Quiz ──────────────────────────────────────────────────────────
        attempts_qs = QuizAttempt.objects.filter(
            quiz__user=user,
            created_at__gte=since
        )
        if doc_id:
            attempts_qs = attempts_qs.filter(quiz__document_id=doc_id)

        quiz_stats = attempts_qs.aggregate(
            average_score=Avg("score"),
            total_attempts=Count("id")
        )

        # ── Stockage ──────────────────────────────────────────────────────
        storage = {
            "used_bytes": user.used_storage_bytes,
            "max_bytes": user.max_storage_bytes,
            "percentage": round(
                (user.used_storage_bytes / user.max_storage_bytes * 100)
                if user.max_storage_bytes > 0 else 0, 1
            )
        }

        return Response({
            "period_days": days,
            "documents": {
                "total": documents_count,
                "ready": documents_ready,
            },
            "learning_time_seconds": total_time,
            "storage": storage,
            "quiz": {
                "average_score": round(quiz_stats["average_score"] or 0, 2),
                "total_attempts": quiz_stats["total_attempts"],
            },
        })


class ProgressView(APIView):
    """
    GET /api/analytics/progress/
    Courbe de progression : score moyen par jour sur la période.
    Filtre : ?days=30
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request)
        since = timezone.now() - timedelta(days=days)

        # Récupère les tentatives et groupe par date
        attempts = (
            QuizAttempt.objects
            .filter(quiz__user=user, created_at__gte=since)
            .values("created_at__date")
            .annotate(avg_score=Avg("score"), count=Count("id"))
            .order_by("created_at__date")
        )

        progression = [
            {
                "date": str(a["created_at__date"]),
                "average_score": round(a["avg_score"], 2),
                "attempts": a["count"],
            }
            for a in attempts
        ]

        return Response({"progression": progression, "period_days": days})


class ConceptsView(APIView):
    """
    GET /api/analytics/concepts/
    Scores par type de question / concept.
    Retourne les 3 concepts les plus faibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request)
        since = timezone.now() - timedelta(days=days)

        # Agrège les réponses par chunk_index (proxy pour "concept")
        answers = (
            Answer.objects
            .filter(
                attempt__quiz__user=user,
                attempt__created_at__gte=since,
                question__chunk_index__isnull=False
            )
            .values("question__chunk_index", "question__quiz__document__title")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True))
            )
            .order_by("correct")
        )

        concepts = []
        for a in answers:
            rate = round((a["correct"] / a["total"] * 100) if a["total"] else 0, 1)
            concepts.append({
                "chunk_index": a["question__chunk_index"],
                "document": a["question__quiz__document__title"],
                "success_rate": rate,
                "total_questions": a["total"],
                "correct_answers": a["correct"],
            })

        weakest = sorted(concepts, key=lambda c: c["success_rate"])[:3]

        return Response({
            "concepts": concepts,
            "weakest_concepts": weakest,
        })


class RecommendationsView(APIView):
    """
    GET /api/analytics/recommendations/
    Génère des recommandations de révision basées sur les concepts faibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request)
        since = timezone.now() - timedelta(days=days)

        # Concepts faibles = taux de succès < 60%
        answers = (
            Answer.objects
            .filter(
                attempt__quiz__user=user,
                attempt__created_at__gte=since,
                question__chunk_index__isnull=False
            )
            .values("question__chunk_index", "question__quiz__document_id",
                    "question__quiz__document__title")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True))
            )
        )

        recommendations = []
        for a in answers:
            rate = (a["correct"] / a["total"] * 100) if a["total"] else 0
            if rate < 60:
                recommendations.append({
                    "document_id": a["question__quiz__document_id"],
                    "document_title": a["question__quiz__document__title"],
                    "chunk_index": a["question__chunk_index"],
                    "success_rate": round(rate, 1),
                    "recommendation": (
                        f"Révisez le passage #{a['question__chunk_index']} "
                        f"du document « {a['question__quiz__document__title']} » "
                        f"(taux de réussite : {rate:.0f}%)."
                    )
                })

        # Trier par taux le plus faible en premier
        recommendations.sort(key=lambda r: r["success_rate"])

        return Response({
            "recommendations": recommendations[:10],
            "period_days": days,
        })


class ExportCSVView(APIView):
    """
    GET /api/analytics/export/csv/
    Exporte les résultats de quiz au format CSV.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request, default=90)
        since = timezone.now() - timedelta(days=days)

        attempts = QuizAttempt.objects.filter(
            quiz__user=user,
            created_at__gte=since
        ).select_related("quiz", "quiz__document").order_by("-created_at")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Quiz", "Document", "Score (%)"])

        for a in attempts:
            writer.writerow([
                a.created_at.strftime("%Y-%m-%d %H:%M"),
                a.quiz.title,
                a.quiz.document.title,
                round(a.score, 2),
            ])

        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="progression.csv"'
        return response


class ExportPDFView(APIView):
    """
    GET /api/analytics/export/pdf/
    Exporte les résultats de quiz au format PDF.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = _parse_days(request, default=90)
        since = timezone.now() - timedelta(days=days)

        attempts = QuizAttempt.objects.filter(
            quiz__user=user,
            created_at__gte=since
        ).select_related("quiz", "quiz__document").order_by("-created_at")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph(f"Rapport de Progression - {user.get_full_name() or user.email}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Table data
        data = [["Date", "Quiz", "Document", "Score (%)"]]
        for a in attempts:
            data.append([
                a.created_at.strftime("%Y-%m-%d %H:%M"),
                a.quiz.title[:30] + '...' if len(a.quiz.title) > 30 else a.quiz.title,
                a.quiz.document.title[:30] + '...' if len(a.quiz.document.title) > 30 else a.quiz.document.title,
                f"{round(a.score, 2)}%"
            ])

        # Table style
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(t)
        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="progression.pdf"'
        response.write(pdf)
        
        return response
