from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, Answer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "choice_text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "question_type", "question_text", "chunk_index", "choices"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "document", "title", "difficulty", "questions", "created_at"]
        read_only_fields = ["id", "questions", "created_at"]


class QuizGenerateSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    difficulty = serializers.ChoiceField(choices=Quiz.Difficulty.choices, default=Quiz.Difficulty.MEDIUM)
    num_questions = serializers.IntegerField(min_value=5, max_value=50, default=10)
    question_types = serializers.ListField(
        child=serializers.ChoiceField(choices=Question.Type.choices),
        default=["MCQ", "BOOLEAN", "OPEN"]
    )


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_choice_id = serializers.IntegerField(required=False, allow_null=True)
    open_answer_text = serializers.CharField(required=False, allow_blank=True)


class QuizSubmitSerializer(serializers.Serializer):
    answers = AnswerSubmitSerializer(many=True)


class SingleAnswerSaveSerializer(serializers.Serializer):
    """Pour la sauvegarde continue : une seule réponse à la fois."""
    question_id = serializers.IntegerField(required=True)
    selected_choice_id = serializers.IntegerField(required=False, allow_null=True)
    open_answer_text = serializers.CharField(required=False, allow_blank=True, default="")


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "status", "score", "created_at", "submitted_at"]
        read_only_fields = fields
