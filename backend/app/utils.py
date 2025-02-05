import os
import uuid
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.runnables import RunnableWithMessageHistory, RunnableLambda
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.database import create_chat, save_message, fetch_chat_messages, fetch_all_chats
from typing import List, Dict
from langchain.retrievers.multi_query import MultiQueryRetriever
from operator import itemgetter

VECTOR_STORE_NAME = "simple-rag"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_DIR = "./vector_store"

def get_llm(model="qwen2.5:1.5b", temperature=0.5):
    return OllamaLLM(model=model, temperature=temperature)
llm = get_llm()
def generate_chat_id():
    return str(uuid.uuid4())

def create_retriever(vector_db, llm):
    """Create a multi-query retriever."""
    if not hasattr(vector_db, 'as_retriever'):
        raise ValueError("Invalid vector DB instance")
    base_retriever = vector_db.as_retriever(
        search_type="mmr",  # Maximal Marginal Relevance
        search_kwargs={
            "k": 5,  # Number of docs to retrieve
            "lambda_mult": 0.25  # Diversity parameter
        }
    )
    prompt_template = """
    You are an AI language model assistant. Your task is to generate five
    different versions of the given user question to retrieve relevant documents from
    a vector database. By generating multiple perspectives on the user question, your
    goal is to help the user overcome some of the limitations of the distance-based
    similarity search. Provide these alternative questions separated by newlines.
    Original question: {question}
    """

    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=ChatPromptTemplate.from_template(prompt_template),
        parser_key="lines"
    )
    print("Retriever created.")
    return retriever

def create_vector_db(chunks=None, chat_id=None):
    """Create or load a vector database."""
    if not chat_id:
        raise ValueError("chat_id is required to create a vector DB")
    
    vector_store_path = os.path.join(VECTOR_STORE_DIR, chat_id)

    if chunks:
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
            persist_directory=vector_store_path,
        )
        print(f"Stored {len(chunks)} document chunks for chat_id {chat_id}.")
    else:
        # Load an existing vector database
        return Chroma(
            persist_directory=vector_store_path,
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),  # Corrected parameter
        )
    return vector_db

def create_chain(retriever, llm):
    """Create a RAG (Retrieve-then-Generate) chain."""
    template = """Answer the question based on the following context:


    Context:
    {context}

    Question: {question}

    Strict Rules:
    1. Base your answer strictly on the context
    2. If unclear, ask for clarification
    """

    def format_docs(docs):
        # Add debug print
        print(f"\n=== Retrieved {len(docs)} documents ===")
        for i, doc in enumerate(docs[:3]):  # Print first 3 docs
            print(f"Document {i+1} ({len(doc.page_content)} chars):")
            print(doc.page_content[:200] + "...")
            print(f"Metadata: {doc.metadata}\n")
        return "\n\n".join([d.page_content for d in docs])
    
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {
            "context": RunnableLambda(lambda x: x["question"]) | retriever | format_docs,
            "question": RunnableLambda(lambda x: x["question"])
        }
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
    
    def format_history(self) -> str:
        """Format chat history into a string for use in prompts."""
        history_str = ""
        for msg in self.messages:
            if msg["role"] == "user":
                history_str += f"User: {msg['content']}\n"
            elif msg["role"] == "ai":
                history_str += f"AI: {msg['content']}\n"
        return history_str.strip()



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

def load_conversations(llm):
    conversations = {}
    all_chats = fetch_all_chats()
    for chat_id, title in all_chats:
        print(f"Loading messages for chat_id: {chat_id}")
        memory = ChatMessageHistory()
        messages = fetch_chat_messages(chat_id)
        for msg in messages:
            memory.add_message({"role": msg["role"], "content": msg["content"]})
        
        def get_session_history():
            print(f"Returning session history for chat_id {chat_id}: {memory.messages}")
            return memory
        
        prompt_template = """
        You are an offline chatbot for OHCHR internal use. Provide accurate and contextual answers in English, Arabic, or Russian. 
        Your task is to provide accurate responses based on the user inqueries.
        

        Conversation so far:
        {history}

        User: {input}
        AI:
        """
        system_message = SystemMessage(content="You are a helpful AI assistant.")
        
        conversation = RunnableWithMessageHistory(
            llm,
            history=memory,
            system_message=system_message,
            prompt_template=prompt_template,
            get_session_history=get_session_history,  # Pass memory to restore session history
        )
        
        # Store the reconstructed conversation object
        conversations[chat_id] = {
            "conversation": conversation,
            "memory": memory,
            "title": title,
        }
    return conversations