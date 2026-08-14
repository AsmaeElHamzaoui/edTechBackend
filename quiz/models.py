from django.db import models
from django.conf import settings
from documents.models import Document


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "EASY", "Facile"
        MEDIUM = "MEDIUM", "Moyen"
        HARD = "HARD", "Difficile"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, related_name="quizzes")
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    created_at = models.DateTimeField(auto_now_add=True)


class Question(models.Model):
    class Type(models.TextChoices):
        MCQ = "MCQ", "QCM"
        BOOLEAN = "BOOLEAN", "Vrai/Faux"
        OPEN = "OPEN", "Question Ouverte"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(max_length=20, choices=Type.choices)
    question_text = models.TextField()
    chunk_index = models.PositiveIntegerField(null=True, blank=True)

    # Explication pédagogique de la réponse
    explanation = models.TextField(blank=True)

    # Uniquement pour les questions ouvertes (la réponse modèle de l'IA)
    expected_answer = models.TextField(blank=True)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    choice_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)


class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        SUBMITTED = "SUBMITTED", "Soumis"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)


class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Pour QCM et BOOLEAN
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)

    # Pour OPEN
    open_answer_text = models.TextField(blank=True)

    # Résultats de la correction
    is_correct = models.BooleanField(default=False)
    ai_correction = models.TextField(blank=True)  # Retour spécifique de l'IA pour question ouverte
    ai_score = models.FloatField(null=True, blank=True)  # Score sémantique 0-1 pour les questions ouvertes
