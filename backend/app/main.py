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

llm = get_llm()

# Initialize database
init_db()
conversations = load_conversations(llm)

# Instantiate the LLM model

# Include routes
app.include_router(chat_routes.router, prefix="/chat", tags=["Chat"])
app.include_router(history_routes.router, prefix="/history", tags=["History"])
app.include_router(file_routes.router, prefix="/upload", tags=["Upload"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)