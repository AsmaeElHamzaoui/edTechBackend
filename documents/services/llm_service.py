from google import genai
from django.conf import settings


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def generate_answer(
    question,
    context,
    conversation_history=""
):

    prompt = f"""
Tu es un assistant pédagogique.

Tu dois répondre à la question de l'apprenant
UNIQUEMENT à partir du CONTEXTE fourni.

Tu peux utiliser l'HISTORIQUE DE CONVERSATION
uniquement pour comprendre les références
et le contexte de la question.

Si la réponse n'est pas présente dans le contexte,
réponds exactement :

"Je ne trouve pas cette information dans le document fourni."

Ne complète pas avec tes connaissances générales.
Ne devine pas.

========================
HISTORIQUE DE CONVERSATION
========================

{conversation_history}

========================
QUESTION ACTUELLE
========================

{question}

========================
CONTEXTE RAG
========================

{context}

========================
RÉPONSE
========================
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text