import json
from google import genai
from django.conf import settings
from quiz.models import Answer

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def evaluate_open_answer(answer: Answer):
    prompt = f"""
Tu es un évaluateur expert.
Question posée à l'apprenant : {answer.question.question_text}
Réponse attendue (modèle) : {answer.question.expected_answer}
Réponse de l'apprenant : {answer.open_answer_text}

Évalue la réponse de l'apprenant. Sois juste. Si l'idée générale est bonne, considère la réponse comme correcte.
Réponds UNIQUEMENT en JSON, sans balise markdown.
Format attendu :
{{
    "is_correct": true, // ou false
    "correction": "Explication pédagogique des erreurs ou validation de la réponse."
}}
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    
    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    data = json.loads(raw_text.strip())
    
    answer.is_correct = data.get("is_correct", False)
    answer.ai_correction = data.get("correction", "")
    answer.save(update_fields=["is_correct", "ai_correction"])
