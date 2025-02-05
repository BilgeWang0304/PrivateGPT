from pydantic import BaseModel



class ChatRequest(BaseModel):
    chat_id: str | None
    message: str

class ChatResponse(BaseModel):
    chat_id: str
    response: dict

class ChatHistoryResponse(BaseModel):
    chat_id: str
    history: list

class ChatSummary(BaseModel):
    chat_id: str
    title: str

class ChatDetail(BaseModel):
    chat_id: str
    messages: list[dict]

class RenameChatRequest(BaseModel):
    title: str

class VectorDBState:
    def __init__(self):
        self.vector_db = None
    
    def set_vector_db(self, db):
        self.vector_db = db
    
    def get_vector_db(self):
        return self.vector_db

vector_db_state = VectorDBState()