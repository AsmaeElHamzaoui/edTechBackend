from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from documents.models import Document
from .models import Quiz, Question, Choice, QuizAttempt, Answer
from .serializers import (
    QuizSerializer, QuizGenerateSerializer, QuizSubmitSerializer,
    SingleAnswerSaveSerializer, AttemptSerializer,
)
from .services.generator_service import generate_quiz_questions
from .services.evaluation_service import evaluate_open_answer


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        serializer = QuizGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_id = serializer.validated_data["document_id"]
        document = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)

        if document.status != Document.Status.READY:
            return Response({"detail": "Document not ready."}, status=status.HTTP_400_BAD_REQUEST)

        # ── Difficulté adaptative ──────────────────────────
        difficulty = serializer.validated_data["difficulty"]
        
        # Analyser les 3 dernières tentatives de l'utilisateur
        from django.db.models import Avg
        recent_attempts = QuizAttempt.objects.filter(
            user=request.user,
            status=QuizAttempt.Status.SUBMITTED
        ).order_by('-submitted_at')[:3]

        if recent_attempts.count() == 3:
            avg_score = recent_attempts.aggregate(Avg('score'))['score__avg']
            if avg_score >= 80.0 and difficulty != Quiz.Difficulty.HARD:
                difficulty = Quiz.Difficulty.HARD
            elif avg_score < 40.0 and difficulty != Quiz.Difficulty.EASY:
                difficulty = Quiz.Difficulty.EASY

        quiz = Quiz.objects.create(
            user=request.user,
            document=document,
            title=serializer.validated_data["title"],
            difficulty=difficulty
        )

        try:
            generate_quiz_questions(
                quiz=quiz,
                num_questions=serializer.validated_data["num_questions"],
                question_types=serializer.validated_data["question_types"]
            )
            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            quiz.delete()
            return Response({"detail": f"Génération échouée: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ──────────────────────────────────────────────
    # Sauvegarde continue : démarrer une tentative
    # ──────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="start-attempt")
    def start_attempt(self, request, pk=None):
        """
        POST /api/quiz/{id}/start-attempt/
        Crée une tentative IN_PROGRESS ou retourne celle en cours.
        """
        quiz = self.get_object()

        # Vérifier s'il existe déjà une tentative en cours
        existing = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()

        if existing:
            # Retourner la tentative existante avec ses réponses déjà sauvegardées
            saved_answers = existing.answers.select_related("question", "selected_choice").all()
            answers_data = [
                {
                    "question_id": a.question_id,
                    "selected_choice_id": a.selected_choice_id,
                    "open_answer_text": a.open_answer_text,
                }
                for a in saved_answers
            ]
            return Response({
                "attempt": AttemptSerializer(existing).data,
                "saved_answers": answers_data,
            })

        attempt = QuizAttempt.objects.create(
            quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
        )
        return Response({
            "attempt": AttemptSerializer(attempt).data,
            "saved_answers": [],
        }, status=status.HTTP_201_CREATED)

    # ──────────────────────────────────────────────
    # Sauvegarde continue : sauvegarder UNE réponse
    # ──────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="save-answer")
    def save_answer(self, request, pk=None):
        """
        POST /api/quiz/{id}/save-answer/
        Body: { "question_id": ..., "selected_choice_id": ..., "open_answer_text": "..." }
        Sauvegarde ou met à jour une réponse dans la tentative en cours.
        """
        quiz = self.get_object()
        serializer = SingleAnswerSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()

        if not attempt:
            return Response({"detail": "Aucune tentative en cours."}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(Question, id=serializer.validated_data["question_id"], quiz=quiz)

        # Upsert : mettre à jour si la réponse existe déjà, sinon créer
        answer, created = Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "selected_choice_id": serializer.validated_data.get("selected_choice_id"),
                "open_answer_text": serializer.validated_data.get("open_answer_text", ""),
            }
        )

        return Response({"detail": "Réponse sauvegardée.", "created": created})

    # ──────────────────────────────────────────────
    # Soumission finale
    # ──────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        POST /api/quiz/{id}/submit/
        Soumet les réponses via body OU finalise la tentative en cours.
        Si des réponses sont fournies dans le body, elles sont utilisées.
        Sinon, les réponses sauvegardées progressivement sont utilisées.
        """
        quiz = self.get_object()

        # Chercher une tentative en cours
        attempt = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()

        # Si des réponses sont fournies dans le body (mode classique)
        body_serializer = QuizSubmitSerializer(data=request.data)
        has_body_answers = body_serializer.is_valid() and body_serializer.validated_data.get("answers")

        if has_body_answers:
            if not attempt:
                attempt = QuizAttempt.objects.create(
                    quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
                )
            # Sauvegarder les réponses du body
            for ans_data in body_serializer.validated_data["answers"]:
                question = get_object_or_404(Question, id=ans_data["question_id"], quiz=quiz)
                Answer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        "selected_choice_id": ans_data.get("selected_choice_id"),
                        "open_answer_text": ans_data.get("open_answer_text", ""),
                    }
                )

        if not attempt:
            return Response({"detail": "Aucune tentative en cours."}, status=status.HTTP_400_BAD_REQUEST)

        # ── Correction ────────────────────────────────────
        correct_count = 0
        total_questions = quiz.questions.count()
        results = []

        for answer in attempt.answers.select_related("question", "selected_choice").all():
            question = answer.question

            if question.question_type in [Question.Type.MCQ, Question.Type.BOOLEAN]:
                if answer.selected_choice:
                    answer.is_correct = answer.selected_choice.is_correct
                    answer.save(update_fields=["is_correct"])

            elif question.question_type == Question.Type.OPEN:
                evaluate_open_answer(answer)

            if answer.is_correct:
                correct_count += 1

            results.append({
                "question_id": question.id,
                "is_correct": answer.is_correct,
                "explanation": question.explanation,
                "ai_correction": answer.ai_correction,
                "expected_answer": question.expected_answer,
            })

        attempt.score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        attempt.status = QuizAttempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["score", "status", "submitted_at"])

        # ── Notification ──────────────────────────────────
        try:
            from agents.notification_agent import NotificationAgent
            NotificationAgent.notify_quiz_result(request.user, quiz, attempt.score)
        except Exception:
            pass

        return Response({
            "attempt_id": attempt.id,
            "score": attempt.score,
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "results": results,
        })
