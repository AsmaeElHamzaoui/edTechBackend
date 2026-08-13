from quiz.models import Quiz, Question
from quiz.services.generator_service import generate_quiz_questions
from quiz.serializers import QuizSerializer

class QuizAgent:
    """
    Agent spécialisé dans la création d'évaluations et quiz.
    """
    
    @staticmethod
    def execute(user, document, text: str):
        
        # On crée un quiz par défaut via l'agent
        quiz = Quiz.objects.create(
            user=user,
            document=document,
            title="Quiz généré par l'Agent",
            difficulty=Quiz.Difficulty.MEDIUM
        )
        
        try:
            generate_quiz_questions(
                quiz=quiz,
                num_questions=5,
                question_types=["MCQ", "BOOLEAN"]
            )
            
            serializer = QuizSerializer(quiz)
            
            return {
                "agent": "QuizAgent",
                "intent": "QUIZ",
                "data": serializer.data
            }
            
        except Exception as e:
            quiz.delete()
            return {
                "agent": "QuizAgent",
                "intent": "QUIZ",
                "error": str(e)
            }
