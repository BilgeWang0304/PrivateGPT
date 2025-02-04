import os
import logging
import pymupdf
from langchain.schema import Document
from fastapi import APIRouter, HTTPException, File, UploadFile
from app.utils import create_vector_db, get_llm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models import vector_db_state
from app.globals import chat_file_mapping
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import asyncio


router = APIRouter()
process_executor = ThreadPoolExecutor(max_workers=3)
llm = get_llm()
UPLOAD_FOLDER = "./uploads"
VECTOR_STORE_DIR = "./vector_store"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
shared_vector_db = None
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
EMBEDDING_MODEL = "nomic-embed-text"

def extract_text_pymupdf(pdf_path):
    """Extract text from a PDF using PyMuPDF (fitz)."""
    doc = pymupdf.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    if not text.strip():
        raise ValueError("No text found in the PDF.")
    return text

async def process_pdf(chat_id: str, file_path: str, filename: str):
    """Process PDF with thread pooling for CPU-bound tasks"""
    try:
        # Run blocking operations in thread pool
        text = await asyncio.get_event_loop().run_in_executor(
            process_executor,
            lambda: extract_text_pymupdf(file_path)
        )
        print("PDF loaded successfully.")

        document = await asyncio.get_event_loop().run_in_executor(
            process_executor,
            lambda: Document(page_content=text, metadata={"source": filename})
        )

        chunks = await asyncio.get_event_loop().run_in_executor(
            process_executor,
            lambda: RecursiveCharacterTextSplitter(
                chunk_size=1200, 
                chunk_overlap=200
            ).split_documents([document])
        )
        print("PDF split into chunks.")

        # Create vector DB
        vector_db = await asyncio.get_event_loop().run_in_executor(
            process_executor,
            lambda: create_vector_db(chunks, chat_id=chat_id)
        )

        # Update state
        vector_db_state.set_vector_db(vector_db)
        chat_file_mapping.setdefault(chat_id, []).append(file_path)

        return True
    except Exception as e:
        logging.error(f"Processing error: {e}")
        raise

@router.post("/{chat_id}")
async def upload_file(chat_id: str, file: UploadFile = File(...)):
    """Upload endpoint with guaranteed completion before response"""
    try:
        # Create upload directory
        chat_upload_dir = os.path.join(UPLOAD_FOLDER, chat_id)
        os.makedirs(chat_upload_dir, exist_ok=True)
        file_path = os.path.join(chat_upload_dir, file.filename)

        # Async file save
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await file.read())

        # Process with async wrapper
        success = await process_pdf(chat_id, file_path, file.filename)
        
        if not success:
            raise HTTPException(500, "File processing failed")

        return {"message": f"File processed successfully."}

    except Exception as e:
        logging.error(f"Upload error: {e}")
        raise HTTPException(500, "File processing failed") from e

