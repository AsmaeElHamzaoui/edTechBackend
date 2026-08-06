from google import genai
from django.conf import settings


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def rewrite_question(question, conversation_history=""):

    if not conversation_history:
        return question

    prompt = f"""
Tu es un assistant qui reformule les questions
pour un système RAG.

Tu dois transformer la QUESTION ACTUELLE en une
question autonome qui peut être comprise sans
connaître l'historique de conversation.

Utilise uniquement l'historique pour comprendre
les références comme :
- il
- elle
- ce projet
- ce concept
- pourquoi
- comment
- celui-ci
- cette information

Ne réponds PAS à la question.

Retourne uniquement la question reformulée.

HISTORIQUE :

{conversation_history}

QUESTION ACTUELLE :

{question}

QUESTION AUTONOME :
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text.strip()
