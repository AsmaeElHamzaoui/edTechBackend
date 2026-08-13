from google import genai
from django.conf import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class EvaluationAgent:
    """
    Agent d'évaluation : corrige les réponses ouvertes
    de manière sémantique via le LLM.
    """

    @staticmethod
    def evaluate_open_answer(question_text: str, expected_answer: str,
                             student_answer: str, document_context: str = "") -> dict:
        """
        Évalue une réponse ouverte et renvoie score, correction et explication.
        """
        prompt = f"""
Tu es un correcteur pédagogique expert.
Évalue la réponse de l'apprenant par rapport à la réponse attendue.

QUESTION :
{question_text}

RÉPONSE ATTENDUE :
{expected_answer}

CONTEXTE DU DOCUMENT (extrait) :
{document_context[:2000]}

RÉPONSE DE L'APPRENANT :
{student_answer}

INSTRUCTIONS :
- Évalue si la réponse est correcte, partiellement correcte ou incorrecte.
- Donne un score entre 0 et 1 (ex: 1.0 = parfait, 0.5 = partiel, 0.0 = faux).
- Fournis une correction concise et bienveillante.
- Indique la source dans le document si possible.

Réponds en JSON avec exactement ces champs :
{{
  "score": <float entre 0 et 1>,
  "is_correct": <true si score >= 0.6, false sinon>,
  "correction": "<explication courte et bienveillante>",
  "source_hint": "<indication sur où trouver l'info dans le document>"
}}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        import json, re
        raw = response.text.strip()
        # Extract JSON from response
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return {
                    "agent": "EvaluationAgent",
                    "score": float(result.get("score", 0)),
                    "is_correct": bool(result.get("is_correct", False)),
                    "correction": result.get("correction", ""),
                    "source_hint": result.get("source_hint", ""),
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback si parsing échoue
        return {
            "agent": "EvaluationAgent",
            "score": 0.0,
            "is_correct": False,
            "correction": raw,
            "source_hint": "",
        }

    @staticmethod
    def execute(question_text: str, expected_answer: str,
                student_answer: str, document_context: str = "") -> dict:
        return EvaluationAgent.evaluate_open_answer(
            question_text, expected_answer, student_answer, document_context
        )
