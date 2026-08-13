from documents.services.summary_service import generate_document_summary

class SummaryAgent:
    """
    Agent spécialisé dans la génération de résumés.
    """
    
    @staticmethod
    def execute(document, text: str):
        
        # L'agent peut affiner le type en fonction de la requête (fiche vs résumé simple)
        summary_type = "summary"
        if "fiche" in text.lower() or "synthèse" in text.lower():
            summary_type = "study_sheet"
            
        summary_text = generate_document_summary(document, summary_type)
        
        return {
            "agent": "SummaryAgent",
            "intent": "SUMMARY",
            "data": {
                "document_id": document.id,
                "type": summary_type,
                "content": summary_text
            }
        }
