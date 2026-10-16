from database.models import ChatHistory

def get_conversation_context(conversation_id, limit=10):
    """
    Retrieves the last `limit` messages for a given conversation from the database
    and formats them as OpenAI message dictionaries.
    """
    if not conversation_id:
        return []
        
    history = ChatHistory.query.filter_by(conversation_id=conversation_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    
    # We get them descending, so we need to reverse them to chronological order
    history.reverse()
    
    context_messages = []
    for chat in history:
        context_messages.append({"role": "user", "content": chat.message})
        context_messages.append({"role": "assistant", "content": chat.response})
        
    return context_messages
