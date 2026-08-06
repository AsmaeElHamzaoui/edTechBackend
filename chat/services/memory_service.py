from chat.models import Conversation, Message


def create_conversation(user, document=None, title=""):
    return Conversation.objects.create(
        user=user,
        document=document,
        title=title
    )


def add_message(conversation, role, content):
    return Message.objects.create(
        conversation=conversation,
        role=role,
        content=content
    )


def get_conversation_history(conversation, limit=10):

    messages = (
        conversation.messages
        .order_by("-created_at")[:limit]
    )

    return list(reversed(messages))


def build_conversation_history(conversation, limit=10):

    messages = get_conversation_history(
        conversation,
        limit=limit
    )

    history = []

    for message in messages:
        history.append(
            f"{message.role.upper()}: {message.content}"
        )

    return "\n\n".join(history)