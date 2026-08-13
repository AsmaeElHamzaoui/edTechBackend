from google import genai
from django.conf import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class OrchestratorAgent:
    """
    Agent principal (Orchestrateur) — 6 agents supportés :
    1. RAG Agent         → QUESTION
    2. Pedagogical Agent → EXPLAIN
    3. Quiz Agent        → QUIZ
    4. Summary Agent     → SUMMARY
    5. Evaluation Agent  → EVALUATE
    6. Notification Agent→ NOTIFY
    """

    @staticmethod
    def classify_intent(text: str) -> str:
        prompt = f"""
Tu es l'Orchestrateur d'une plateforme EdTech intelligente.
Analyse la requête de l'apprenant et détermine son intention principale.
Choisis UNE SEULE des catégories suivantes :

- QUESTION   → question sur un contenu, un concept ou un document
- EXPLAIN    → demande d'explication, de simplification ou d'approfondissement
- SUMMARY    → demande de résumé, fiche de synthèse ou récapitulatif
- QUIZ       → demande de quiz, test, exercice ou évaluation
- EVALUATE   → soumission d'une réponse à corriger ou évaluer
- NOTIFY     → demande liée aux notifications ou rappels
- UNKNOWN    → hors sujet ou non reconnu

Réponds UNIQUEMENT avec le mot exact (ex: QUESTION). Aucun autre texte.

Requête apprenant : {text}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip().upper()

    @staticmethod
    def process(user, document, text: str, level: str = "normal") -> dict:
        intent = OrchestratorAgent.classify_intent(text)

        if "QUESTION" in intent:
            from .rag_agent import RagAgent
            return RagAgent.execute(user, document, text)

        elif "EXPLAIN" in intent:
            from .pedagogical_agent import PedagogicalAgent
            return PedagogicalAgent.execute(document, text, level=level)

        elif "SUMMARY" in intent:
            from .summary_agent import SummaryAgent
            return SummaryAgent.execute(document, text)

        elif "QUIZ" in intent:
            from .quiz_agent import QuizAgent
            return QuizAgent.execute(user, document, text)

        elif "EVALUATE" in intent:
            # L'apprenant soumet une réponse libre à évaluer
            from .evaluation_agent import EvaluationAgent
            return EvaluationAgent.execute(
                question_text=text,
                expected_answer="",   # À fournir via paramètre si disponible
                student_answer=text,
                document_context=document.extracted_text[:3000] if document.extracted_text else ""
            )

        elif "NOTIFY" in intent:
            from .notification_agent import NotificationAgent
            return NotificationAgent.execute(user, notification_type="GENERIC")

        else:
            return {
                "agent": "Orchestrator",
                "intent": "UNKNOWN",
                "message": (
                    "Je ne suis pas sûr de comprendre votre demande. "
                    "Vous pouvez poser une question, demander une explication, "
                    "un résumé ou un quiz sur votre document."
                )
            }
