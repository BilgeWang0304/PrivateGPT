from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, ChatResponse, ChatSummary, ChatDetail
from app.utils import create_new_conversation, get_llm, save_conversations, load_conversations
from langchain.chains import RetrievalQA
from app.database import save_message, get_db_connection
import asyncio

router = APIRouter()

# Instantiate the LLM model using the utility function
llm = get_llm()
VECTOR_STORE_DIR = "./vector_store"
EMBEDDING_MODEL = "nomic-embed-text"

# Load conversations from storage
conversations = load_conversations(llm)

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print("Received request:", request)
        chat_id = request.chat_id or create_new_conversation(conversations, llm, VECTOR_STORE_DIR, EMBEDDING_MODEL)
        if chat_id not in conversations:
            raise HTTPException(status_code=400, detail="Invalid chat_id. Please start a new conversation.")
        
        conversation = conversations.get(chat_id, {}).get("conversation")
        if not conversation:
            raise HTTPException(status_code=500, detail="Conversation object not found.")
        
        memory = conversations[chat_id]["memory"]

        # Add user message to memory in the correct format
        user_message = {"role": "user", "content": request.message}
        memory.add_message(user_message)
        print(f"Added user message to memory: {memory.messages}")

        response_text = ""

        async def generate_response_stream():
            nonlocal response_text
            try:
                print("Starting response streaming...")
                for token in conversation.stream(request.message):  
                    response_text += token  
                    yield token  
                    await asyncio.sleep(0.01)  
                
                if conversations[chat_id]["title"] == "New Chat":
                    new_title = request.message[:30] or "Untitled Chat"

                    # Update in-memory title
                    conversations[chat_id]["title"] = new_title

                    # Persist title update in the database
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (new_title, chat_id))
                        conn.commit()
                    print(f"Chat title updated to: {new_title}")

                if response_text.strip():  # Ensure response_text is not empty
                    ai_message = {"role": "ai", "content": response_text}
                    memory.add_message(ai_message)
                    print(f"Added AI message to memory: {ai_message}")

                    save_message(chat_id, "user", request.message)
                    save_message(chat_id, "ai", response_text)
                    save_conversations(chat_id, memory)
                else:
                    print("Response text is empty. Skipping save_message.")
            except Exception as e:
                print(f"Error during streaming: {e}")
                yield f"Error generating response: {str(e)}"

        return StreamingResponse(
            generate_response_stream(),
            media_type="text/plain"
        )
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/new_chat")
async def new_chat():
    try:
        chat_id = create_new_conversation(conversations, llm, VECTOR_STORE_DIR, EMBEDDING_MODEL)
        return {"chat_id": chat_id}
    except Exception as e:
        print("Error creating a new chat:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats", response_model=list[ChatSummary])
async def get_chats():
    try:
        chat_summaries = [{"chat_id": chat_id, "title": data["title"]} for chat_id, data in conversations.items()]
        return chat_summaries
    except Exception as e:
        print("Error fetching chats:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat_history(chat_id: str):
    if chat_id not in conversations:
        raise HTTPException(status_code=404, detail="Chat ID not found.")
    memory = conversations[chat_id]["memory"]
    print("Memory object1:", memory)  # Debug print to check memory object
    messages = []
    for message in memory.messages:
        print("Message object:", message)  # Debug print to check each message
        messages.append({"role": message.role, "content": message.content})
    return {"chat_id": chat_id, "messages": messages}