from chat.services.memory_service import (
    add_message,
    build_conversation_history
)

from documents.services.rag_service import (
    build_rag_context
)

from documents.services.llm_service import (
    generate_answer
)

from chat.services.query_rewriter import (
    rewrite_question
)


def ask_question(conversation, question):

    # --------------------------------------------------
    # 1. Récupérer l'historique AVANT d'ajouter
    #    la nouvelle question
    # --------------------------------------------------

    history = build_conversation_history(
        conversation,
        limit=10
    )

    # --------------------------------------------------
    # 2. Reformuler la question avec la mémoire
    # --------------------------------------------------

    search_question = rewrite_question(
        question,
        history
    )

    # --------------------------------------------------
    # 3. Sauvegarder la question originale
    # --------------------------------------------------

    add_message(
        conversation,
        "user",
        question
    )

    # --------------------------------------------------
    # 4. Récupérer le document
    # --------------------------------------------------

    document_id = None

    if conversation.document:
        document_id = conversation.document.id

    # --------------------------------------------------
    # 5. Recherche RAG avec la question reformulée
    # --------------------------------------------------

    rag_result = build_rag_context(
        search_question,
        n_results=3,
        document_id=document_id
    )

    # --------------------------------------------------
    # 6. Génération de la réponse
    # --------------------------------------------------

    answer = generate_answer(
        question,
        rag_result["context"],
        history
    )

    # --------------------------------------------------
    # 7. Sauvegarder la réponse
    # --------------------------------------------------

    add_message(
        conversation,
        "assistant",
        answer
    )

    # --------------------------------------------------
    # 8. Retour API
    # --------------------------------------------------

    return {
        "conversation_id": conversation.id,
        "question": question,
        "answer": answer,
        "sources": rag_result["sources"]
    }