## PrivateGPT - Offline Chatbot for Secure Data Analysis

🚀 A locally hosted AI-based chatbot with file analysis capabilities, built using FastAPI and React, supportted by Ollama.


## Overview

An internal, offline-capable chatbot solution combining:

- **Backend**: Python FastAPI for AI processing and API endpoints

- **Frontend**: React.js for modern user interface

- **AI Stack**: Ollama for local LLM operations + LangChain for RAG pipeline

- **Security**: Complete data isolation with offline document processing

- **Multilingual**: 29 languages available, including English, Russian, Arabic

Ideal for sensitive internal communications where data privacy is paramount.

## Key Features

### ➡️ Real-Time Streaming Responses

Instant answer generation with typing indicator

Streamed content delivery for natural conversation flow

### ➡️ Secure Document Intelligence (RAG)

Local file processing with LangChain integration

PDF/TXT document analysis without cloud exposure

Context-aware responses using private knowledge bases

### ➡️ Multi-User Workspaces

Isolated chat sessions with persistent history

Role-based access control framework

Concurrent user support with resource optimization

### ➡️ Offline-First Architecture

Complete airgap capability

Local LLM management via Ollama (Qwen/DeepSeek)

Zero third-party data sharing

## Installation & Setup

### Prerequisites

Python 3.9+

Node.js 16+

Ollama service running locally

### 1. Backend Setup
```bash
# Clone repository
git clone https://github.com/BilgeWang0304/PrivateGPT.git
cd PrivateGPT/backend

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd PrivateGPT/frontend
npm install  # Install dependencies
npm start  # Run the frontend
```

### 3. Ollama Setup

From https://ollama.com/ install Ollama.

After installation, open the terminal to install required LLMs.

