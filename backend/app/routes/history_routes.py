from fastapi import APIRouter, HTTPException
from app.models import ChatSummary, ChatDetail, RenameChatRequest
from app.database import get_db_connection

router = APIRouter()

@router.get("/", response_model=list[ChatSummary])
async def get_chats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, title FROM chats')
        chats = cursor.fetchall()
        conn.close()
        return [{"chat_id": chat_id, "title": title} for chat_id, title in chats]
    except Exception as e:
        print("Error fetching chats:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat_history(chat_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, content 
            FROM messages 
            WHERE chat_id = ? 
            ORDER BY created_at ASC
        ''', (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            raise HTTPException(status_code=404, detail="Chat ID not found.")
        
        # Properly format the messages before returning
        formatted_messages = [{"role": role, "content": content} for role, content in messages]
        print(f"Fetched messages for chat_id {chat_id}.") 
        return {"chat_id": chat_id, "messages": formatted_messages}
    except Exception as e:
        print("Error fetching chat history:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": f"Chat {chat_id} deleted successfully."}
    except Exception as e:
        print(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting chat.")
    
@router.put("/{chat_id}/rename")
async def rename_chat(chat_id: str, request: RenameChatRequest):
    try: 
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (request.title, chat_id))
        conn.commit()
        conn.close()

        return {"message": "Chat renamed successfully."}
    except Exception as e:
        print("Error renaming chat:", str(e))
        raise HTTPException(status_code=500, detail="Failed to rename chat.")