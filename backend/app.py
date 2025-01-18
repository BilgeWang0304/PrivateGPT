from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain.llms import Ollama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import uuid

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Ollama
llm = Ollama(model="llama3.2", temperature=0.3)

# Store all conversations
conversations = {}

# Request model
class ChatRequest(BaseModel):
    chat_id: str | None
    message: str

# Helper: Create a new conversation
def create_new_conversation():
    chat_id = str(uuid.uuid4())
    memory = ConversationBufferMemory()
    prompt_template = PromptTemplate(
        input_variables=["history", "input"],
        template="""
        You are a helpful AI assistant. Engage in a conversation with the user.

        Conversation so far:
        {history}

        User: {input}
        AI:
        """
    )
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt_template
    )
    conversations[chat_id] = {
        "conversation": conversation,
        "title": "New Chat"
    }
    return chat_id

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print("Received request:", request)
        chat_id = request.chat_id or create_new_conversation()
        conversation = conversations[chat_id]["conversation"]

        response = await conversation.apredict(input=request.message)

        if conversations[chat_id]["title"] == "New Chat":
            conversations[chat_id]["title"] = request.message[:30]

        return {"chat_id": chat_id, "response": response}
    except Exception as e:
        print("Error:", str(e))
        return {"error": str(e)}

# Endpoint to get all conversations
@app.get("/chats")
async def get_chats():
    return [{"chat_id": chat_id, "title": data["title"]} for chat_id, data in conversations.items()]
