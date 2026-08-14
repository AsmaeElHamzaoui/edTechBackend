from google import genai
from django.conf import settings
from documents.models import Document

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def generate_document_summary(document: Document, summary_type="summary"):
    """
    Génère un résumé ou une fiche de synthèse du document via Gemini.
    """
    content = document.extracted_text

    if summary_type == "study_sheet":
        prompt_instruction = "Crée une fiche de synthèse pédagogique très structurée (avec titres, tirets, points clés, et définitions importantes) à partir de ce document."
    else:
        prompt_instruction = "Rédige un résumé clair, complet et concis de ce document, en mettant en évidence les idées principales."

    prompt = f"""
Tu es un assistant pédagogique expert.
{prompt_instruction}

Règle absolue : Base-toi UNIQUEMENT sur le contenu du document fourni ci-dessous. N'invente aucune information. Si le document ne contient pas de sens clair, signale-le.

========================
CONTENU DU DOCUMENT
========================

{content}

========================
RÉPONSE
========================
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text
