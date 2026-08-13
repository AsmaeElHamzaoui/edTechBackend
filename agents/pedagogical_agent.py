from google import genai
from django.conf import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class PedagogicalAgent:
    """
    Agent pédagogique : explique un concept, simplifie une notion,
    ou approfondit un sujet à partir du contenu du document.
    """

    LEVELS = {
        "simple": "un enfant de 12 ans sans connaissance du sujet",
        "normal": "un étudiant universitaire",
        "expert": "un expert du domaine",
    }

    @staticmethod
    def execute(document, text: str, level: str = "normal") -> dict:
        audience = PedagogicalAgent.LEVELS.get(level, PedagogicalAgent.LEVELS["normal"])

        # Utilise le texte extrait du document comme contexte
        context = document.extracted_text[:4000] if document.extracted_text else ""

        prompt = f"""
Tu es un professeur expert et pédagogue.
Tu dois expliquer ou développer le sujet demandé par l'apprenant.
Adapte ton explication pour {audience}.

DOCUMENT DE RÉFÉRENCE (extrait) :
{context}

DEMANDE DE L'APPRENANT :
{text}

CONSIGNES :
- Base-toi sur le document si possible.
- Utilise des exemples concrets adaptés au niveau.
- Structure ta réponse avec des titres si nécessaire.
- Si la notion n'est pas dans le document, indique-le clairement.

EXPLICATION :
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "agent": "PedagogicalAgent",
            "intent": "EXPLAIN",
            "data": {
                "document_id": document.id,
                "level": level,
                "content": response.text,
            }
        }
