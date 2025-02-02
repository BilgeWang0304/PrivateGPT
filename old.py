main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat_routes, history_routes, file_routes
from app.database import init_db
from app.utils import get_llm, load_conversations

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()
conversations = load_conversations()

# Instantiate the LLM model
llm = get_llm()

# Include routes
app.include_router(chat_routes.router, prefix="/chat", tags=["Chat"])
app.include_router(history_routes.router, prefix="/history", tags=["History"])
app.include_router(file_routes.router, prefix="/upload", tags=["Upload"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
utils.py
import os
import uuid
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.database import create_chat, save_message, fetch_chat_messages, fetch_all_chats
from typing import List, Dict

VECTOR_STORE_DIR = "./vector_store"
EMBEDDING_MODEL = "nomic-embed-text"

def get_llm(model="qwen2.5:1.5b", temperature=0.2, max_tokens=300):
    return OllamaLLM(model=model, temperature=temperature, max_tokens=max_tokens)

def generate_chat_id():
    return str(uuid.uuid4())

def create_vector_db(chunks=None):
    """Create or load a vector database."""
    if chunks:
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            persist_directory=VECTOR_STORE_DIR,
        )
        return vector_db
    else:
        # Load an existing vector database
        return Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        )
    
def create_standard_retriever(vector_db):
    """Create a standard retriever for vector search."""
    return vector_db.as_retriever()

def create_chain(retriever, llm):
    """Create a RAG (Retrieve-then-Generate) chain."""
    template = """Answer the question based ONLY on the following context:
{context}
Question: {question}"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

class ChatMessageHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, message: Dict):
        if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
            raise ValueError('Got unsupported message type: {}'.format(message))
        self.messages.append(message)
    
    def to_base_messages(self):
        """Convert message history to a list of BaseMessages."""
        base_messages = []
        for msg in self.messages:
            if msg["role"] == "user":
                base_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                base_messages.append(AIMessage(content=msg["content"]))
            else:
                raise ValueError(f"Unsupported message role: {msg['role']}")
        return base_messages



def create_new_conversation(conversations, llm, vector_store_dir, embedding_model):
    chat_id = generate_chat_id()
    memory = ChatMessageHistory()
    print(f"Initialized memory object: {memory}")

    def get_session_history():
        print(f"Returning session history: {memory} ({type(memory)}) with messages: {memory.messages}")
        return memory
    
    prompt_template = """
    You are an offline chatbot for OHCHR internal use. Provide accurate and contextual answers in English, Arabic, or Russian. 

    Conversation so far:
    {history}

    User: {input}
    AI:
    """

    print("Initializing RunnableWithMessageHistory...")
    conversation = RunnableWithMessageHistory(
        llm,
        history=memory,
        system_message=SystemMessage(content="You are a helpful AI assistant."),
        prompt_template=prompt_template,
        get_session_history=get_session_history,
    )

    conversations[chat_id] = {
        "conversation": conversation,
        "memory": memory,
        "title": "New Chat"
    }
    create_chat(chat_id, "New Chat")
    return chat_id

def save_conversations(chat_id, memory):
    for message in memory.messages:
        save_message(chat_id, message["role"], message["content"])

def load_conversations():
    conversations = {}
    all_chats = fetch_all_chats()
    for chat_id, title in all_chats:
        print(f"Loading messages for chat_id: {chat_id}")
        memory = ChatMessageHistory()
        messages = fetch_chat_messages(chat_id)
        for msg in messages:
            memory.add_message({"role": msg["role"], "content": msg["content"]})
        conversations[chat_id] = {
            "title": title,
            "memory": memory
        }
    return conversations
database.py
import sqlite3
from typing import List, Dict, Tuple

DATABASE = "chat_data.db"

def init_db():
    """Initialize the database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
            )
        """)
        conn.commit()

def get_db_connection():
    """Get a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    return conn

def create_chat(chat_id: str, title: str = "New Chat", ):
    """Insert a new chat into the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (chat_id, title) VALUES (?, ?)", (chat_id, title))
        conn.commit()

def save_message(chat_id: str, role: str, content: str):
    """Save a message to the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        print(f"Saved message for chat_id {chat_id}: role={role}, content={content}")  # Debug print
        conn.commit()

def fetch_chat_messages(chat_id: str) -> List[Dict]:
    """Fetch all messages for a given chat ID."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
        messages = cursor.fetchall()
    return [{"role": role, "content": content} for role, content in messages]

def fetch_all_chats() -> List[Tuple[str, str]]:
    """Fetch all chat IDs and titles."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, title FROM chats ORDER BY created_at DESC")
        return cursor.fetchall()
    
def delete_all_data():
    """Delete all data from the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")  # Delete all messages
        cursor.execute("DELETE FROM chats")    # Delete all chats
        conn.commit()
        print("All data has been deleted from the database.")
chat_routes.py
from fastapi import APIRouter, HTTPException
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
conversations = load_conversations()

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
        input_message = request.message
        if not isinstance(input_message, str):
            raise HTTPException(status_code=400, detail="Input message must be a string.")
        print(f"Input to conversation.invoke: {input_message} ({type(input_message)})")

        # Call the synchronous conversation.invoke
        print("Calling conversation.invoke synchronously...")
        response = conversation.invoke(input_message)
        print(f"Generated response: {response}")

        if conversations[chat_id]["title"] == "New Chat":
            new_title = request.message[:40] or "Untitled Chat"

            # Update in-memory title
            conversations[chat_id]["title"] = new_title

            # Persist title update in the database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (new_title, chat_id))
                conn.commit()
            print(f"Chat title updated to: {new_title}")

        print(f"Generated response: {response}")

        # Add AI response to memory in the correct format
        ai_message = {"role": "ai", "content": str(response)}
        memory.add_message(ai_message)
        print(f"Added AI message to memory: {memory.messages}")

        # Save the user query and AI response
        save_message(chat_id, "user", request.message)
        save_message(chat_id, "ai", str(response))

        save_conversations(chat_id, memory)  # Save after generating response

        return {"chat_id": chat_id, "response": {"query": request.message, "result": str(response)}}
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
history_routes.py
from fastapi import APIRouter, HTTPException
from app.models import ChatSummary, ChatDetail
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
        cursor.execute('SELECT role, content FROM messages WHERE chat_id = ? ORDER BY created_at', (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            raise HTTPException(status_code=404, detail="Chat ID not found.")
        
        # Properly format the messages before returning
        formatted_messages = [{"role": role, "content": content} for role, content in messages]
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
    


from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, ChatSummary, ChatDetail
from app.utils import create_new_conversation, save_conversations
from app.database import save_message
import asyncio
from asyncio import Lock
from app import globals  # Import the globals module for shared state

router = APIRouter()

lock = Lock()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        async with lock:
            conversations = globals.conversations
            llm = globals.llm

        if conversations is None:
            raise HTTPException(status_code=500, detail="Conversations not initialized")
        if llm is None:
            raise HTTPException(status_code=500, detail="LLM not initialized")

        # Create a new conversation or use an existing one
        chat_id = request.chat_id or await create_new_conversation(conversations, llm, globals.VECTOR_STORE_DIR, globals.EMBEDDING_MODEL)
        if chat_id not in conversations:
            raise HTTPException(status_code=400, detail="Invalid chat_id. Please start a new conversation.")

        # Get the specific conversation
        conversation = conversations[chat_id]["conversation"]
        memory = conversations[chat_id]["memory"]

        # Process user input
        user_message = {"role": "user", "content": request.message}
        memory.add_message(user_message)

        # Generate AI response
        print(f"Debug: Starting conversation.invoke with message: {request.message}")
        response = await asyncio.to_thread(conversation.invoke, request.message)
        print(f"Debug: Received response from conversation.invoke: {response}")

        # Add AI response to memory
        ai_message = {"role": "ai", "content": str(response)}
        memory.add_message(ai_message)

        # Save data asynchronously
        await asyncio.gather(
            save_message(chat_id, "user", request.message),
            save_message(chat_id, "ai", str(response)),
            save_conversations(chat_id, memory)
        )

        return {"chat_id": chat_id, "response": {"query": request.message, "result": str(response)}}
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new_chat")
async def new_chat():
    try:
        # Ensure globals are initialized
        if globals.conversations is None or globals.llm is None:
            raise HTTPException(status_code=500, detail="Conversations or LLM not initialized")

        chat_id = await create_new_conversation(globals.conversations, globals.llm, globals.VECTOR_STORE_DIR, globals.EMBEDDING_MODEL)
        return {"chat_id": chat_id}
    except Exception as e:
        print("Error creating a new chat:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats", response_model=list[ChatSummary])
async def get_chats():
    try:
        if globals.conversations is None:
            raise HTTPException(status_code=500, detail="Conversations not initialized")

        chat_summaries = [{"chat_id": chat_id, "title": data["title"]} for chat_id, data in globals.conversations.items()]
        return chat_summaries
    except Exception as e:
        print("Error fetching chats:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat_history(chat_id: str):
    try:
        if globals.conversations is None:
            raise HTTPException(status_code=500, detail="Conversations not initialized")
        if chat_id not in globals.conversations:
            raise HTTPException(status_code=404, detail="Chat ID not found.")

        memory = globals.conversations[chat_id]["memory"]
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in memory.messages]
        return {"chat_id": chat_id, "messages": messages}
    except Exception as e:
        print("Error fetching chat history:", str(e))
        raise HTTPException(status_code=500, detail=str(e))



from fastapi import APIRouter, HTTPException
from app.models import ChatSummary, ChatDetail
from app.database import get_db_connection, get_db_path
import aiosqlite
import asyncio

router = APIRouter()

@router.get("/", response_model=list[ChatSummary])
async def get_chats():
    """Fetch all chats from the database."""
    try:
        print("Debug: Starting database query for chats.")
        async with await get_db_connection() as conn:
            print("Debug: Database connection established.")
            def fetch_chats():
                cursor = conn.cursor()
                cursor.execute('SELECT chat_id, title FROM chats')
                return cursor.fetchall()

            print("Debug: Fetching chats using asyncio.to_thread.")
            chats = await asyncio.to_thread(fetch_chats)
            print(f"Debug: Successfully fetched chats: {chats}")
        return [{"chat_id": chat_id, "title": title} for chat_id, title in chats]
    except Exception as e:
        print("Error fetching chats:", str(e))
        raise HTTPException(status_code=500, detail="Error fetching chat summaries.")


@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat_history(chat_id: str):
    """Fetch the message history for a specific chat."""
    try:
        async with await get_db_connection() as conn:
            async with conn.execute(
                'SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id', 
                (chat_id,)
            ) as cursor:
                messages = await cursor.fetchall()
        
        if not messages:
            raise HTTPException(status_code=404, detail="Chat ID not found.")
        
        # Properly format the messages before returning
        formatted_messages = [{"role": role, "content": content} for role, content in messages]
        return {"chat_id": chat_id, "messages": formatted_messages}
    except Exception as e:
        print("Error fetching chat history:", str(e))
        raise HTTPException(status_code=500, detail="Error fetching chat history.")


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat and its associated messages from the database."""
    try:
        async with await get_db_connection() as conn:
            await conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            await conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
            await conn.commit()
        
        return {"message": f"Chat {chat_id} deleted successfully."}
    except Exception as e:
        print(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting chat {chat_id}.")


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat_routes, history_routes, file_routes
from app.database import init_db
from app.utils import get_llm, load_conversations
from app import globals
import asyncio

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database

@app.on_event("startup")
async def startup_event():
    """Initialize the database and load conversations on startup."""
    await init_db()
    globals.conversations = await load_conversations()  # Update global conversations
    globals.llm = get_llm()  # Update global LLM
    print("Conversations initialized:", globals.conversations)
    print("LLM initialized:", globals.llm)

@app.on_event("shutdown")
async def shutdown_event():
    print("Executor shutdown complete.")

# Include routes
app.include_router(chat_routes.router, prefix="/chat", tags=["Chat"])
app.include_router(history_routes.router, prefix="/history", tags=["History"])
app.include_router(file_routes.router, prefix="/upload", tags=["Upload"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)



import aiosqlite
from typing import List, Dict, Tuple
import os

DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "chat_data.db"))

def get_db_path():
    """Return the absolute path to the database file."""
    return os.path.abspath(DATABASE)

async def get_db_connection():
    """Get a connection to the database asynchronously."""
    try:
        print("Debug: Attempting to create a new database connection.")
        conn = await aiosqlite.connect(DATABASE)
        print("Debug: Successfully created database connection.")
        return conn
    except Exception as e:
        print(f"Error in get_db_connection: {e}")
        raise

async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
            )
        """)
        await conn.commit()

async def create_chat(chat_id: str, title: str = "New Chat"):
    """Insert a new chat into the database."""
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute("INSERT INTO chats (chat_id, title) VALUES (?, ?)", (chat_id, title))
        await conn.commit()

async def save_message(chat_id: str, role: str, content: str):
    """Save a message to the database."""
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        print(f"Saved message for chat_id {chat_id}: role={role}, content={content}")  # Debug print
        await conn.commit()

async def fetch_chat_messages(chat_id: str) -> List[Dict]:
    """Fetch all messages for a given chat ID."""
    async with aiosqlite.connect(DATABASE) as conn:
        cursor = await conn.execute(
            "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", 
            (chat_id,)
        )
        rows = await cursor.fetchall()
    return [{"role": role, "content": content} for role, content in rows]

async def fetch_all_chats() -> List[Tuple[str, str]]:
    """Fetch all chat IDs and titles."""
    async with aiosqlite.connect(DATABASE) as conn:
        cursor = await conn.execute("SELECT chat_id, title FROM chats ORDER BY created_at DESC")
        rows = await cursor.fetchall()
    return rows

async def delete_all_data():
    """Delete all data from the database."""
    async with aiosqlite.connect(DATABASE) as conn:
        await conn.execute("DELETE FROM messages")  # Delete all messages
        await conn.execute("DELETE FROM chats")    # Delete all chats
        await conn.commit()
        print("All data has been deleted from the database.")




import os
import uuid
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.database import create_chat, save_message, fetch_chat_messages, fetch_all_chats
from typing import List, Dict

VECTOR_STORE_DIR = "./vector_store"
EMBEDDING_MODEL = "nomic-embed-text"


def get_llm(model="qwen2.5:1.5b", temperature=0.2, max_tokens=200):
    """Instantiate the LLM model with given parameters."""
    return OllamaLLM(model=model, temperature=temperature, max_tokens=max_tokens)


def generate_chat_id():
    """Generate a unique ID for a new chat session."""
    return str(uuid.uuid4())


def create_vector_db(chunks=None):
    """Create or load a vector database."""
    if chunks:
        return Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            persist_directory=VECTOR_STORE_DIR,
        )
    else:
        # Load an existing vector database
        return Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        )


def create_standard_retriever(vector_db):
    """Create a standard retriever for vector search."""
    return vector_db.as_retriever()


def create_chain(retriever, llm):
    """Create a RAG (Retrieve-then-Generate) chain."""
    template = """Answer the question based ONLY on the following context:
{context}
Question: {question}"""

    prompt = ChatPromptTemplate.from_template(template)

    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


class ChatMessageHistory:
    """A class to manage chat message history."""
    def __init__(self):
        self.messages = []

    def add_message(self, message: Dict):
        """Add a message to the history."""
        if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
            raise ValueError(f"Unsupported message type: {message}")
        self.messages.append(message)

    def to_base_messages(self):
        """Convert message history to a list of BaseMessages."""
        base_messages = []
        for msg in self.messages:
            if msg["role"] == "user":
                base_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                base_messages.append(AIMessage(content=msg["content"]))
            else:
                raise ValueError(f"Unsupported message role: {msg['role']}")
        return base_messages


async def create_new_conversation(conversations, llm, vector_store_dir, embedding_model):
    """Create a new conversation and add it to the conversations dictionary."""
    chat_id = generate_chat_id()
    memory = ChatMessageHistory()
    print(f"Initialized memory object for chat_id {chat_id}")

    def get_session_history():
        """Return the session history for the conversation."""
        return memory

    prompt_template = """
    You are an offline chatbot for OHCHR internal use. Provide accurate and contextual answers in English, Arabic, or Russian. 

    Conversation so far:
    {history}

    User: {input}
    AI:
    """

    conversation = RunnableWithMessageHistory(
        llm,
        history=memory,
        system_message=SystemMessage(content="You are a helpful AI assistant."),
        prompt_template=prompt_template,
        get_session_history=get_session_history,
    )

    conversations[chat_id] = {
        "conversation": conversation,
        "memory": memory,
        "title": "New Chat"
    }

    # Persist the new chat to the database
    await create_chat(chat_id, "New Chat")
    return chat_id


async def save_conversations(chat_id, memory):
    """Save the chat conversation history to the database."""
    for message in memory.messages:
        await save_message(chat_id, message["role"], message["content"])


async def load_conversations():
    """Load all conversations from the database."""
    conversations = {}
    all_chats = await fetch_all_chats()

    for chat_id, title in all_chats:
        print(f"Loading messages for chat_id: {chat_id}")
        memory = ChatMessageHistory()
        messages = await fetch_chat_messages(chat_id)
        for msg in messages:
            memory.add_message({"role": msg["role"], "content": msg["content"]})
        conversations[chat_id] = {
            "title": title,
            "memory": memory
        }

    return conversations



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

        async def generate_response_stream():
            try:
                for token in conversation.invoke(request.message):  # Get the full response as a string
                    yield token  # Send each token as it is generated
                    await asyncio.sleep(0.01)
            except Exception as e:
                yield f"Error generating response: {str(e)}"

        streaming_response = StreamingResponse(
            generate_response_stream(),
            media_type="text/plain"
        )

        if conversations[chat_id]["title"] == "New Chat":
            new_title = request.message[:24] or "Untitled Chat"

            # Update in-memory title
            conversations[chat_id]["title"] = new_title

            # Persist title update in the database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (new_title, chat_id))
                conn.commit()
            print(f"Chat title updated to: {new_title}")

        print(f"Generated response.")

        # Add AI response to memory in the correct format
        ai_message = {"role": "ai", "content": str(streaming_response)}
        memory.add_message(ai_message)
        print(f"Added AI message to memory.")

        # Save the user query and AI response
        save_message(chat_id, "user", request.message)
        save_message(chat_id, "ai", str(streaming_response))

        save_conversations(chat_id, memory)  # Save after generating response

        return streaming_response
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    

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
                    yield token  # Send each token as it is generated
                    await asyncio.sleep(0.1)
            except Exception as e:
                yield f"Error generating response: {str(e)}"

        token_accumulator = []
        async for token in generate_response_stream():
            token_accumulator.append(token)
            yield token 

        response_text = "".join(token_accumulator)
        print(f"Final response_text after streaming: {response_text}")

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

        print(f"Generated response.")

        # Add AI response to memory in the correct format
        ai_message = {"role": "ai", "content": response_text}
        memory.add_message(ai_message)
        print(f"Added AI message to memory.")

        # Save the user query and AI response
        save_message(chat_id, "user", request.message)
        save_message(chat_id, "ai", response_text)

        save_conversations(chat_id, memory)  # Save after generating response

        return StreamingResponse((token for token in token_accumulator), media_type="text/plain")
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))