import os
import logging
import pymupdf
from langchain.schema import Document
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from app.utils import create_vector_db, create_retriever, create_chain, get_llm
from langchain_text_splitters import RecursiveCharacterTextSplitter


router = APIRouter()

llm = get_llm()
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
shared_vector_db = None

def extract_text_pymupdf(pdf_path):
    """Extract text from a PDF using PyMuPDF (fitz)."""
    doc = pymupdf.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    if not text.strip():
        raise ValueError("No text found in the PDF.")
    return text

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF file and process it into the vector database."""
    global shared_vector_db
    try:
        # Save the uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load and split the PDF
        text = extract_text_pymupdf(file_path)
        print("PDF loaded successfully.")

        document = Document(page_content=text, metadata={"source": file.filename})
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
        chunks = text_splitter.split_documents([document])
        print("PDF split into chunks.")

        # Create the vector database
        shared_vector_db = create_vector_db(chunks)
        return {"message": "File uploaded and processed successfully."}
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the file.")

@router.post("/query/")
async def query_file(question: str = Form(...)):
    """Query the vector database."""
    global shared_vector_db
    if shared_vector_db is None:
        raise HTTPException(status_code=400, detail="No file has been uploaded.")

    try:
        retriever = create_retriever(shared_vector_db)
        chain = create_chain(retriever, llm)

        # Run the query
        relevant_docs = retriever.invoke(question)
        if not relevant_docs:
            return {"response": "No relevant data found in the document."}
        document_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        print (f"Retrieved {len(relevant_docs)} chunks for query.")
        query_with_context = f"Context: {document_text}\n\nQuestion: {question}"
        response = chain.invoke({"question": query_with_context})
        return {"response": response}
    except Exception as e:
        logging.error(f"Error querying file: {e}")
        raise HTTPException(status_code=500, detail="Failed to query the file.")