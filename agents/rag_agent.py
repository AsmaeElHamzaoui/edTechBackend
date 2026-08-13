from chat.models import Conversation
from chat.services.chat_service import ask_question

class RagAgent:
    """
    Agent spécialisé dans la réponse aux questions via RAG.
    """
    
    @staticmethod
    def execute(user, document, text: str):
        # Pour une demande générique de l'orchestrateur, on crée ou récupère 
        # une conversation temporaire (ou la plus récente) pour le document
        conversation = Conversation.objects.filter(
            user=user, 
            document=document
        ).order_by("-updated_at").first()
        
        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                document=document,
                title=text[:255]
            )
            
        # Appel au service existant du chat
        result = ask_question(conversation, text)
        
        return {
            "agent": "RagAgent",
            "intent": "QUESTION",
            "data": result
        }
