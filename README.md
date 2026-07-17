# PlaceMentor AI

> 🎓 Intelligent placement mentorship system for LPU students, powered by multi-agent AI + RAG.

## Architecture

```
FastAPI Backend ← LangGraph Agent Graph ← Groq LLM (llama-3.3-70b)
       ↓                                        ↓
 PostgreSQL DB                          Gemini 1.5 Flash (resume)
       ↓
  Redis (session)
       ↓
  ChromaDB (vector store)
```

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Docker Desktop
- Git

### 2. Clone & Setup

```bash
git clone <repo>
cd placementor

# Start infrastructure (Postgres, Redis, ChromaDB)
docker-compose up postgres redis chromadb -d
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and fill in your API keys
copy .env.example .env
# Edit .env with your GROQ_API_KEY and GOOGLE_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

### 4. Get API Keys (all free)

| Key | Where to get |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free tier |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) — free tier |
| `LANGCHAIN_API_KEY` | [smith.langchain.com](https://smith.langchain.com) — optional, for tracing |

### 5. Ingest Knowledge Base

```bash
# Place your LPU documents in knowledge_base/ subdirectories
# Then run the ingestor:
python -m rag.ingestor --dir ../knowledge_base/placement_policies --collection placement_policies
python -m rag.ingestor --dir ../knowledge_base/company_jds --collection company_jds
python -m rag.ingestor --dir ../knowledge_base/learning_resources --collection learning_resources
```

### 6. API Documentation

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register student |
| POST | `/api/v1/auth/login` | Login & get token |
| POST | `/api/v1/chat/message` | Chat with PlaceMentor AI |
| POST | `/api/v1/chat/stream` | Streaming chat (SSE) |
| GET | `/api/v1/chat/history` | Get chat history |
| POST | `/api/v1/resume/upload` | Upload resume |
| GET | `/api/v1/students/me` | Get my profile |
| PATCH | `/api/v1/students/me/profile` | Update my profile |
| GET | `/api/v1/students/me/roadmap` | Get active roadmap |
| GET | `/api/v1/students/me/interviews` | Get interview history |

## Project Structure

```
placementor/
├── backend/
│   ├── main.py              ← FastAPI app
│   ├── config.py            ← Settings
│   ├── auth.py              ← JWT utilities
│   ├── agents/
│   │   ├── graph.py         ← LangGraph orchestrator ⭐
│   │   ├── planner.py       ← Intent router
│   │   ├── retrieval.py     ← RAG agent
│   │   ├── resume_review.py ← Resume analyzer
│   │   ├── skill_gap.py     ← Gap analyzer
│   │   ├── roadmap.py       ← Roadmap generator
│   │   ├── mock_interview.py← Interview conductor
│   │   └── learning_rec.py  ← Resource recommender
│   ├── rag/
│   │   ├── ingestor.py      ← Document → ChromaDB
│   │   ├── retriever.py     ← Vector search
│   │   └── vector_store.py  ← ChromaDB client
│   ├── memory/
│   │   ├── short_term.py    ← Redis session
│   │   └── long_term.py     ← Postgres helpers
│   ├── database/
│   │   ├── models.py        ← ORM models
│   │   └── session.py       ← DB connection
│   └── routers/
│       ├── auth.py          ← Register/Login
│       ├── chat.py          ← Chat API
│       ├── student.py       ← Profile/Roadmap
│       └── resume.py        ← Upload
├── knowledge_base/          ← Drop documents here
└── docker-compose.yml       ← Infrastructure
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI (Python 3.11) |
| Agent Orchestration | LangGraph |
| Primary LLM | Groq → llama-3.3-70b-versatile |
| Document LLM | Google Gemini 1.5 Flash |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector DB | ChromaDB |
| SQL DB | PostgreSQL (async via asyncpg) |
| Cache/Session | Redis |
| Task Queue | Celery |
| Auth | JWT (python-jose) |

## Next Steps

- [ ] Phase 5: Next.js Frontend (student portal, chat UI, roadmap view)
- [ ] Phase 4: Automated workflows (weekly progress, company announcements)
- [ ] Add more agents: Progress Tracker, Notification Agent
- [ ] Load LPU-specific knowledge base documents
