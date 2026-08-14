import json
from google import genai
from django.conf import settings
from quiz.models import Quiz, Question, Choice

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_quiz_questions(quiz: Quiz, num_questions: int, question_types: list):
    content = quiz.document.extracted_text
    
    prompt = f"""
Tu es un professeur expert. Génère {num_questions} questions de type {', '.join(question_types)} basées UNIQUEMENT sur le document ci-dessous.
Niveau de difficulté : {quiz.difficulty}.

Tu dois répondre UNIQUEMENT avec un tableau JSON valide. Aucun texte avant ou après. N'ajoute pas de formatage markdown (```json).
Format attendu :
[
  {{
    "type": "MCQ", // Utilise exactement "MCQ", "BOOLEAN", ou "OPEN"
    "question": "Texte de la question ?",
    "choices": ["Choix 1", "Choix 2", "Choix 3", "Choix 4"], // 2 choix pour BOOLEAN (Vrai/Faux), vide pour OPEN
    "correct_index": 0, // L'index de la bonne réponse dans choices (0 pour le premier). Mets null pour OPEN.
    "expected_answer": "...", // Réponse modèle pour OPEN (mets null pour MCQ/BOOLEAN)
    "explanation": "Explication pédagogique de la réponse correcte ou du concept abordé."
  }}
]

Document :
{content}
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
    
    for item in data:
        q = Question.objects.create(
            quiz=quiz,
            question_type=item.get("type", "MCQ"),
            question_text=item.get("question", ""),
            explanation=item.get("explanation", "") or "",
            expected_answer=item.get("expected_answer", "") or ""
        )
        if q.question_type in ["MCQ", "BOOLEAN"]:
            choices = item.get("choices", [])
            correct_idx = item.get("correct_index")
            for idx, c_text in enumerate(choices):
                Choice.objects.create(
                    question=q,
                    choice_text=c_text,
                    is_correct=(idx == correct_idx)
                )
