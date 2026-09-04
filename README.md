Autonomous Email Triaging & Support Agent

An AI-powered email automation agent built with Python, LangGraph, LangChain, RAG, FAISS, BM25, BGE Reranking, Hugging Face embeddings, and Groq LLMs.

The system analyzes incoming emails, determines their priority, summarizes their content, extracts action items, decides whether a response is required, retrieves relevant historical email conversations, and generates context-aware reply drafts. A Human-in-the-Loop workflow ensures that generated replies are reviewed before they can be sent.

Features

📧 Email content analysis

🚦 Automatic priority classification: HIGH / MEDIUM / LOW

📝 Email summarization

✅ Action-item extraction

🤖 Automatic response-required detection

🔎 Retrieval-Augmented Generation (RAG)

🧠 Semantic retrieval using FAISS

🔤 Keyword retrieval using BM25

🔀 Hybrid retrieval using Reciprocal Rank Fusion (RRF)

🎯 BGE reranking for improved relevance

✍️ Context-aware reply generation using Groq LLM

🧑‍💻 Human approval before sending replies

⏸️ LangGraph interrupt/resume workflow

💾 LangGraph checkpointing for paused workflows

Architecture

Incoming Email
      │
      ▼
┌─────────────────┐
│ Analyze Email   │
│ Priority        │
│ Summary         │
│ Action Items    │
│ Response Needed │
└────────┬────────┘
         │
         ▼
   Should Respond?
      │       │
     NO      YES
      │       │
      ▼       ▼
     END   Retrieve Context
              │
              ▼
      ┌─────────────────┐
      │ Hybrid Retrieval│
      │ FAISS + BM25    │
      │ RRF + BGE       │
      └────────┬────────┘
               │
               ▼
       Generate Reply
               │
               ▼
       Human Approval
          │    │    │
       Reject Edit Approve
          │    │    │
          ▼    ▼    ▼
         END  Review  Send

Technology Stack

Component

Technology

Programming Language

Python

Agent Workflow

LangGraph

LLM Framework

LangChain

LLM

Groq (llama-3.1-8b-instant)

Embeddings

Hugging Face sentence-transformers/all-MiniLM-L6-v2

Vector Database

FAISS

Keyword Retrieval

BM25

Hybrid Ranking

Reciprocal Rank Fusion (RRF)

Reranker

BAAI bge-reranker-base

Data Processing

Python / LangChain Community

Human-in-the-Loop

LangGraph interrupt()

Checkpointing

LangGraph InMemorySaver

Project Structure

AI_agent_email/
│
├── agent/
│   ├── __init__.py
│   └── graph.py
│
├── vector_stores/
│   ├── llm.py
│   ├── retriever.py
│   ├── vector_store.py
│   │
│   ├── unread/
│   ├── read/
│   └── read_and_replied/
│
├── data/
│   └── ...
│
├── .env
├── requirements.txt
└── README.md

The exact directory structure may evolve as the project is extended with email ingestion and sending functionality.

RAG Pipeline

Historical emails are converted into searchable chunks and indexed using multiple retrieval approaches.

Historical Emails
       │
       ▼
Document Chunking
       │
       ├───────────────┐
       ▼               ▼
     FAISS            BM25
       │               │
       └───────┬───────┘
               ▼
        Hybrid Retrieval
               │
               ▼
              RRF
               │
               ▼
        BGE Reranker
               │
               ▼
      Relevant Context
               │
               ▼
            Groq LLM
               │
               ▼
          Draft Reply

The project uses the same chunks for FAISS and BM25 so that the two retrieval methods operate over the same underlying document units.

LangGraph Workflow

LangGraph manages the state and execution flow of the agent.

The workflow maintains information such as:

email
priority
summary
action_items
requires_response
retrieved_context
draft_reply
approval_status
final_reply
send_status

The current workflow is:

START
  ↓
analyze_email
  ↓
should_respond
  ├── NO → END
  └── YES
       ↓
retrieve_context
       ↓
generate_reply
       ↓
human_approval
       ↓
END

The email-sending node will be connected after the Human-in-the-Loop stage is completed.

Human-in-the-Loop

The agent does not blindly send an LLM-generated response.

LangGraph pauses execution using interrupt() after generating the draft.

The human can:

Approve the generated reply

Edit the reply before approval

Reject the response

The workflow can then resume using LangGraph's Command(resume=...).

This provides a controlled architecture for AI-assisted email automation.

Installation

Clone the repository and create a virtual environment:

git clone <your-repository-url>
cd AI_agent_email

python -m venv .venv

Activate the environment on Windows:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Environment Variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key

Do not commit .env or API keys to GitHub.

Add the following to .gitignore:

.env
.venv/
__pycache__/
*.pyc

Running the LangGraph Agent

From the project root:

python -m agent.graph

Running the module this way ensures that Python resolves the project packages correctly.

Current Status

Completed

Email data preparation

Historical email vector stores

FAISS semantic retrieval

BM25 keyword retrieval

Hybrid RRF retrieval

BGE reranking

Groq LLM integration

Email analysis

Reply generation

LangGraph workflow

Human-in-the-Loop approval mechanism

LangGraph checkpointing prototype

Planned

Connect to real unread-email ingestion

Implement email sending node

Connect approval workflow to email provider

Persistent checkpoint storage

Retrieval evaluation and ranking metrics

Conversation-level retrieval

Production deployment

Monitoring and logging

Design Goals

The project focuses on building an email agent that is:

Context-aware — uses historical email interactions when generating responses.

Retrieval-grounded — uses RAG rather than relying only on the LLM's pretrained knowledge.

Controlled — requires human approval before sending responses.

Modular — separates retrieval, LLM processing, and workflow orchestration.

Extensible — designed to support real email providers and persistent state in later stages.

Disclaimer

This project is intended for learning, experimentation, and portfolio development. Generated email responses should be reviewed by a human before being sent in real-world environments.
