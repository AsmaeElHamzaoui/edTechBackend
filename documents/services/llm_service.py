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
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def generate_answer_stream(question, context, conversation_history="", complexity="normal"):
    """
    Génère la réponse token par token via Gemini streaming.
    Yields des chunks de texte (str) au fur et à mesure.
    """
    
    complexity_prompt = ""
    if complexity == "simple":
        complexity_prompt = "Niveau: SIMPLE. Utilise un vocabulaire très accessible, fais des analogies de la vie quotidienne et sois très pédagogue."
    elif complexity == "expert":
        complexity_prompt = "Niveau: EXPERT. Utilise le vocabulaire technique approprié, va dans les détails complexes et sois concis et professionnel."
    else:
        complexity_prompt = "Niveau: NORMAL. Sois clair, précis, et explique les termes importants."

    prompt = f"""
Tu es un assistant pédagogique.
{complexity_prompt}

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

    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    ):
        if chunk.text:
            yield chunk.text


def generate_follow_up_actions(question, answer):
    """Génère 3 suggestions d'actions de suivi basées sur la réponse."""
    prompt = f"""
Basé sur la question de l'utilisateur et ta réponse, propose exactement 3 actions de suivi pertinentes pour l'apprenant.
Question : {question}
Réponse : {answer}

Réponds UNIQUEMENT avec un tableau JSON valide. Exemple:
[
  {{"label": "Peux-tu m'expliquer plus simplement ?", "action": "simplifier"}},
  {{"label": "Quelles sont les exceptions à cette règle ?", "action": "approfondir"}},
  {{"label": "Génère un mini-quiz sur ça", "action": "quiz"}}
]
"""
    import json
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())
    except Exception:
        return []