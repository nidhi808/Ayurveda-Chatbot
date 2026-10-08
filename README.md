# 🌿 AyurBot — AI-Powered Ayurveda Knowledge Assistant

> **Educational RAG Knowledge System for Authentic Classical Ayurveda with Dual-Layer Safety Guardrails, Hybrid Vector-BM25 Retrieval, Dual-Engine Voice Input (Google Gemini Multimodal STT + On-Device Whisper.cpp), and Multilingual Support (मराठी, हिन्दी, संस्कृतम्, English).**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF.svg)](https://vitejs.dev/)
[![Voice Input](https://img.shields.io/badge/Voice%20STT-Gemini%20%2B%20Whisper.cpp-orange.svg)](https://ai.google.dev/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%203.1%20%2F%202.5%20Flash%20Lite-4285F4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Our Approach & How We Solve It](#-our-approach--how-we-solve-it)
3. [System Architecture](#-system-architecture)
4. [User Flow Diagram](#-user-flow-diagram)
5. [Visual Showcase & Screenshots](#-visual-showcase--screenshots)
6. [Key Features](#-key-features)
7. [Dual-Engine Speech Recognition (Gemini AI + Whisper.cpp)](#-dual-engine-speech-recognition-gemini-ai--whispercpp)
8. [Technology Stack](#-technology-stack)
9. [Project Structure](#-project-structure)
10. [Installation & Setup](#-installation--setup)
11. [API Documentation](#-api-documentation)
12. [Evaluation & Benchmark Results](#-evaluation--benchmark-results)
13. [Medical & Educational Disclaimer](#-medical--educational-disclaimer)

---

## 🎯 Problem Statement

1. **Unreliable Health Information & AI Hallucinations**: Standard general-purpose LLMs frequently hallucinate medicinal facts, fabricate classical quotes, or blend Western allopathic medicine with Ayurvedic concepts without citation.
2. **Inaccessible Traditional Wisdom**: Classical Ayurvedic literature (*Charaka Samhita*, *Sushruta Samhita*, *Ashtanga Hridaya*, and AYUSH Pharmacopoeia monographs) is rich but fragmented and heavily veiled in technical Sanskrit and vernacular terminology.
3. **Medical Safety & Triage Risks**: Users frequently ask chatbots for self-prescriptions, specific pharmaceutical dosages, or treatment for acute emergencies (e.g., severe chest pain, shortness of breath), risking life-threatening delays without proper safety guardrails.
4. **Multilingual & Dialectal Gap**: A large portion of users search using regional languages and Romanized colloquial transliterations (e.g., Marathi: *"khokla sathi aushadh"*, Hindi: *"khasi ke liye dava"*). Traditional search engines fail to map these terms to classical Ayurvedic botanical entries (such as *Kasa*, *Kapha*, *Tulsi*, *Yashtimadhu*, and *Sitopaladi*).

---

## 💡 Our Approach & How We Solve It

AyurBot addresses these challenges through an end-to-end **Retrieval-Augmented Generation (RAG)** pipeline designed specifically for traditional medicine:

- **Curated Authentic Knowledge Corpus**: Grounded strictly in peer-reviewed reference monographs from the **Ministry of AYUSH**, the **Ayurvedic Pharmacopoeia of India (API)**, and classical Samhitas across 6 domain categories (*Herbs, Fundamentals, Doshas, Lifestyle, Classical Texts, Traditional Concepts*).
- **Hybrid Fusion Retrieval (BM25 + Dense Vectors with RRF)**: Combines exact keyword matching (BM25) with semantic embeddings (Dense Vector Search) through **Reciprocal Rank Fusion (RRF)**, supporting Google Gemini 3072d embeddings (`gemini-embedding-001`) with local dense vector fallback.
- **Multilingual Query Expansion**: A comprehensive phonetic and Devanagari glossary automatically detects regional dialects (Marathi, Hindi, Sanskrit) and expands queries like `"khokla sathi aushadh"` into canonical Ayurvedic and botanical descriptors (*kasa, cough, respiratory, tulsi, yashtimadhu, sitopaladi, kapha*).
- **Dual-Layer Medical Safety Guardrails**:
  - *Layer 1 (Input Guardrail)*: Real-time regex and semantic classifier detecting acute medical emergencies and pharmaceutical prescription requests, immediately redirecting to professional care.
  - *Layer 2 (Output Guardrail)*: Post-generation validator verifying grounding, stripping unverified dosage claims, and enforcing mandatory educational disclaimers.
- **Dual-Engine Speech Recognition (Gemini AI + Whisper.cpp)**:
  - **Primary**: Google Gemini Multimodal Audio Transcription (`gemini-3.1-flash-lite` ➔ `gemini-2.5-flash-lite`) offering high-accuracy recognition for Indian English, Hindi, Marathi, and Sanskrit, preserving Ayurvedic botanical names (*Ashwagandha, Tulsi, Shatavari, Giloy, Triphala*) verbatim without hallucination.
  - **Fallback**: On-device C++ inference via `pywhispercpp` (`ggml-tiny.bin`) for complete offline edge processing.
  - **Audio Processing**: Polyphase sinc anti-aliased resampling using the Web Audio API's native `OfflineAudioContext`.
- **Resilient Multi-Model Generation**: Google Gemini 3.1 Flash Lite with seamless failover to Gemini 2.5 Flash Lite, protected by offline classical synthesis and React ErrorBoundary.

---

## 🏛 System Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Client Layer (React 18 + Vite)"]
        UI[Chat Interface & Real-Time Audio Dock]
        WebSpeech[Browser Live Preview SpeechRecognition]
        AudioCtx[OfflineAudioContext Polyphase Sinc Resampler]
        LangSelect[Language Selector - Marathi, Hindi, English, Sanskrit]
        CatBar[Category Filters - Herbs, Doshas, Lifestyle, etc.]
        Modals[Knowledge Explorer & RAG Evaluator]
    end

    subgraph API["⚡ Server Layer (FastAPI Backend)"]
        Router["/api/chat | /api/transcribe | /api/sources | /api/evaluate"]
        Memory["Multi-Turn Memory Store"]
    end

    subgraph Guardrails["🛡️ Safety & Alignment Layer"]
        L1Safety["Layer 1: Input Classifier (Emergency & Prescription Check)"]
        L2Safety["Layer 2: Output Validator & Legal Disclaimer Injection"]
    end

    subgraph SpeechEngine["🎙️ Dual-Engine Speech-to-Text"]
        GeminiSTT["Google Gemini Multimodal STT (gemini-3.1-flash-lite)"]
        WhisperCpp["Local pywhispercpp (whisper.cpp tiny CPU model)"]
    end

    subgraph RAG["🔍 Hybrid Retrieval Engine"]
        QExp["Multilingual Query Expansion Engine"]
        BM25["BM25 Keyword Retriever"]
        Vector["Dense Vector Store (Gemini 3072d + Local Cosine)"]
        RRF["Reciprocal Rank Fusion (RRF Weighted Re-ranking)"]
    end

    subgraph Generation["🧠 Generation Layer"]
        GeminiLLM["Google Gemini 3.1 / 2.5 Flash Lite API"]
        OfflineSynth["Grounded Multilingual Synthesizer (Offline Fallback)"]
    end

    subgraph Corpus["📚 Authentic Ayurveda Corpus"]
        AYUSH["AYUSH / API Monographs (Herbs, Formulations)"]
        Samhita["Classical Samhitas (Charaka, Sushruta, Sharangadhara)"]
        Life["Dinacharya, Ritucharya & Tridosha Principles"]
    end

    UI -->|Mic MediaRecorder WebM Stream| AudioCtx
    AudioCtx -->|16kHz High-Fidelity WAV| Router
    Router -->|POST /api/transcribe| GeminiSTT
    GeminiSTT -.->|Failover| WhisperCpp
    GeminiSTT -->|Verbatim Spoken Words| UI
    UI -->|HTTP Request with Language & Category| Router
    Router --> Memory
    Router --> L1Safety
    L1Safety -->|Unsafe / Emergency| Router
    L1Safety -->|Safe Query| QExp
    QExp --> BM25
    QExp --> Vector
    Corpus --> BM25
    Corpus --> Vector
    BM25 --> RRF
    Vector --> RRF
    RRF -->|Top Grounded Citations| Generation
    Memory -->|Conversation Context| Generation
    Generation --> GeminiLLM
    Generation --> OfflineSynth
    GeminiLLM --> L2Safety
    OfflineSynth --> L2Safety
    L2Safety -->|Structured Response + Verified Sources| Router
    Router -->|JSON Response| UI
```

---

## 🔄 User Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Practitioner
    participant UI as React Web Interface
    participant AudioEngine as Web Audio (OfflineAudioContext)
    participant Backend as FastAPI Backend
    participant GeminiSTT as 🎙️ Gemini 3.1 Multimodal STT
    participant WhisperCpp as 🎙️ Local Whisper.cpp (Offline CPU)
    participant Safety as Safety Guardrails
    participant RAG as Hybrid Retriever (Vector+BM25)
    participant Generator as LLM (Gemini 3.1 / 2.5 Flash Lite)

    User->>UI: Selects Language & Enters Query
    opt Voice Input (Dual-Engine with Live Feedback)
        User->>UI: Clicks Microphone & Speaks Query
        UI-->>User: Live visual indicator (timer, waveform, Web Speech interim typing)
        User->>UI: Clicks "Done Speaking"
        UI->>AudioEngine: Polyphase sinc anti-aliasing resample to 16kHz WAV
        AudioEngine->>Backend: POST /api/transcribe (16kHz WAV)
        alt Gemini Cloud Available
            Backend->>GeminiSTT: Multimodal audio transcription (preserves herb names verbatim)
            GeminiSTT-->>Backend: Accurate transcribed text (e.g., "Ashwagandha")
        else Offline / Local Mode
            Backend->>WhisperCpp: Local CPU inference via pywhispercpp
            WhisperCpp-->>Backend: Offline transcribed text
        end
        Backend-->>UI: Authoritative transcription populates chat input
    end
    UI->>Backend: POST /api/chat { message, language, category }
    Backend->>Safety: Layer 1: Evaluate Input Safety
    alt Emergency / Direct Prescription Query
        Safety-->>Backend: Intercept! Return Emergency / Non-diagnostic notice
        Backend-->>UI: Refusal with Medical Safety Alert
    else Safe Educational Query
        Safety-->>Backend: Passed
        Backend->>RAG: Expand Query (e.g., khokla to classical remedies)
        RAG-->>Backend: Top-K Verified Document Citations (API & Samhitas)
        Backend->>Generator: Generate Grounded Answer (Target Language & Citations)
        Generator-->>Backend: Pure Marathi/Hindi/English Response + Practical Remedies
        Backend->>Safety: Layer 2: Output Validation & Disclaimer Injection
        Backend-->>UI: ChatResponse { answer, sources, followups, language }
    end
    UI-->>User: Displays Formatted Response with Citations, Disclaimer & Follow-ups
    User->>UI: Clicks Source Chip -> Inspects Monograph & AYUSH URL in Modal
```

---

## 📸 Visual Showcase & Screenshots

### 1. Multilingual Ayurvedic Chat & Natural Remedies (मराठी)
AyurBot natively understands Romanized and Devanagari Marathi queries (`"khokla sathi aushadh"`), maps them to classical *Kasa Roga* knowledge, retrieves authentic AYUSH monographs (*Tulsi, Yashtimadhu, Sitopaladi Churna*), and formats fluent Marathi guidance with doshic actions (*कफ-वात शामक*) and botanical details.

![Marathi Ayurvedic Chat](docs/screenshots/marathi_chat.png)

---

### 2. Interactive Knowledge Corpus Explorer
Search and inspect classical Samhita excerpts and AYUSH botanical monographs across 6 distinct categories (*Herbs, Doshas, Fundamentals, Lifestyle, Classical Texts, Traditional Concepts*), complete with properties and direct links to the official Ministry of AYUSH portal.

![Knowledge Corpus Explorer](docs/screenshots/knowledge_explorer.png)

---

### 3. Automated RAG Evaluation & Safety Benchmark
Built-in evaluation modal running 19 standard clinical and classical test queries to verify Retrieval Precision@3 (100%), Safety Detection Accuracy (100%), and Groundedness Score (100%).

![RAG Evaluation Benchmarks](docs/screenshots/evaluation_benchmarks.png)

---

## ✨ Key Features

- **Grounded Natural Language Chat**: Structured responses featuring classical Ayurvedic principles, botanical names, doshic attributes (*Rasa, Guna, Virya, Vipaka*), and modern scientific notes.
- **Multilingual Fluency**:
  - Full support for **मराठी (Marathi)**, **हिन्दी (Hindi / Hinglish)**, **संस्कृतम् (Sanskrit)**, and **English**.
  - Automatic detection of Romanized colloquialisms (e.g., `"khokla sathi aushadh"`, `"pet dard"`, `"neend nahi aati"`).
- **Source Verification & Citations**: Every assistant reply cites authentic monographs with direct links to the official AYUSH portal.
- **Interactive Knowledge Corpus Explorer**: Search and filter all indexed documents across categories (*Herbs, Doshas, Fundamentals, Lifestyle, Classical Texts*).
- **RAG Evaluation Benchmark Dashboard**: In-app evaluation suite testing **Precision@3**, **Safety Detection Accuracy**, and **Groundedness Score** against standard Ayurvedic test queries.
- **Dual-Engine Speech Recognition**: High-accuracy Google Gemini Multimodal STT for botanical terminology + on-device Whisper.cpp for 100% offline edge resilience.
- **Category-Scoped Inquiries**: Filter conversations specifically for *Herbs*, *Doshas*, *Fundamentals*, or *Lifestyle Regimens*.
- **Dynamic Follow-up Recommendations**: Generates logical next questions in the active conversation language.

---

## 🎙️ Dual-Engine Speech Recognition (Gemini AI + Whisper.cpp)

AyurBot implements a resilient, hybrid voice recognition architecture engineered specifically for the phonetic complexities of Indian languages and Ayurvedic botanical nomenclature.

```
                  ┌───────────────────────────────────────────────┐
                  │ 🎙️ User Speaks (English / Hindi / Marathi)    │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │ 🎧 Web Audio API (OfflineAudioContext)        │
                  │    • Sinc Polyphase Resampling (48kHz ➔ 16kHz)│
                  │    • Complete Anti-Aliasing & Low-Pass Filter │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │ 🚀 FastAPI Server (/api/transcribe)           │
                  └───────┬───────────────────────────────┬───────┘
                          │                               │
                Online (Gemini Key)               Offline / Local
                          │                               │
                          ▼                               ▼
      ┌──────────────────────────────────────┐  ┌─────────────────────────────────┐
      │ 🧠 Google Gemini Multimodal STT      │  │ ⚡ On-Device Whisper.cpp (CPU)   │
      │    • gemini-3.1-flash-lite (primary) │  │    • pywhispercpp C++ bindings  │
      │    • gemini-2.5-flash-lite (failover)│  │    • ggml-tiny.bin (~74 MB)     │
      │    • Verbatim Ayurvedic Botanical STT│  │    • 100% Offline, Zero Cloud   │
      └──────────────────────────────────────┘  └─────────────────────────────────┘
```

### 1. Engine 1: Google Gemini Multimodal STT (Primary)
- **Acoustic Botanical Precision**: General-purpose voice engines frequently confuse specialized Sanskrit or Ayurvedic terms. Gemini's multimodal audio models natively recognize terms like *Ashwagandha, Tulsi, Shatavari, Giloy, Triphala, Haritaki, Brahmi, Vata, Pitta, and Kapha* verbatim.
- **Unbiased Verbatim Prompting**: Utilizes a strict, non-primed Speech-to-Text instruction preventing topical hallucinations (such as substituting unsaid home remedies), while actively filtering out silence timestamp artifacts (`00:00`).
- **Multi-Model Cloud Resilience**: Transparent failover chain across `gemini-3.1-flash-lite` and `gemini-2.5-flash-lite` to ensure near-zero downtime.

### 2. Engine 2: Local Whisper.cpp (Offline Edge Fallback)
- **Zero Cloud Latency & Zero API Costs**: When running completely offline, audio is processed locally on CPU via C++ bindings (`pywhispercpp`) with the quantized `ggml-tiny.bin` model (~74.09 MB).
- **Patient Privacy**: Sensitive health queries never leave the practitioner's or patient's workstation.
- **Remote Dispensary Resilience**: Continues working in rural clinics with intermittent or absent internet connectivity.

### 3. Studio-Grade Client Resampling (`OfflineAudioContext`)
- Standard browser downsampling using simple point decimation folds frequencies between 8kHz and 24kHz back into the audible band, causing harsh distortion that ruins consonant recognition.
- AyurBot utilizes the browser's hardware-accelerated **`OfflineAudioContext`**, performing professional polyphase sinc anti-aliasing downsampling to pristine 16 kHz mono WAV before transmission.

### 4. Interactive Live Feedback
- **Real-Time Visual Dock**: Displays an active recording banner with an elapsed seconds timer `(Xs / 20s)`, pulsing audio indicators, and a dedicated **"Done Speaking"** button.
- **Authoritative Transcription**: While native browser Web Speech API provides live interim preview typing, the authoritative Gemini AI transcription automatically finalizes the input box upon recording completion.

---

## 🛠 Technology Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Vanilla CSS Design System with CSS variables, responsive flex/grid, and glassmorphic cards
- **Icons**: Lucide React (`lucide-react`)
- **Audio Processing**: Web Audio API (`OfflineAudioContext` sinc resampler + `MediaRecorder`)
- **Speech Preview**: Native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`)
- **Resilience**: React ErrorBoundary component protecting against runtime rendering crashes

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn ASGI
- **Data Validation**: Pydantic v2
- **Information Retrieval**:
  - Keyword Search: BM25 Okapi (`rank-bm25`)
  - Vector Embeddings: Gemini Embeddings (`gemini-embedding-001`, 3072d) + Local Dense N-Gram Hash Vectorizer (128d) with self-healing auto-reindexing
  - Ranking: Reciprocal Rank Fusion (RRF)
- **Generative AI & Multimodal STT**:
  - Google Gemini 3.1 Flash Lite API (`google-genai` v1.42+)
  - Google Gemini 2.5 Flash Lite API (automatic cloud failover)
  - Grounded Multilingual Synthesis Engine (local classical fallback)
- **Local Audio Processing**:
  - `pywhispercpp` (C++ `whisper.cpp` Python bindings)
  - GGML Tiny model (`ggml-tiny.bin`)
- **Testing**: Pytest, FastAPI TestClient (`httpx`)

---

## 📂 Project Structure

```
Ayurveda-Chatbot/
├── backend/
│   ├── app/
│   │   ├── rag/
│   │   │   ├── bm25_retriever.py      # BM25 Keyword Search Engine
│   │   │   ├── embeddings.py          # Gemini & Local Dense Embedding Service
│   │   │   ├── evaluator.py           # Benchmark Evaluation Suite (Precision, Safety, Grounding)
│   │   │   ├── generator.py           # Gemini LLM & Offline Multilingual Grounded Synthesizer
│   │   │   ├── hybrid_retriever.py    # Reciprocal Rank Fusion (RRF) Hybrid Retrieval
│   │   │   ├── multilingual.py        # Language Detection & Multilingual Query Expansion
│   │   │   ├── transcriber.py         # Whisper.cpp Speech-to-Text Transcriber
│   │   │   └── vector_store.py        # Cosine Similarity Vector Database
│   │   ├── config.py                  # Environment Configuration & Defaults
│   │   ├── main.py                    # FastAPI Endpoints, CORS, Routing & Error Handlers
│   │   ├── memory.py                  # Multi-Turn In-Memory Conversation Storage
│   │   ├── models.py                  # Pydantic Request/Response Data Models
│   │   └── safety.py                  # Dual-Layer Safety Classifier & Medical Disclaimers
│   ├── data/
│   │   ├── corpus/                    # Authentic Ayurveda Knowledge Corpus
│   │   │   ├── classical_texts.json   # Samhita References (Charaka, Sushruta, Vagbhata)
│   │   │   ├── fundamentals.json      # Panchamahabhuta, Tridosha, Prakriti, Agni, Ama
│   │   │   ├── herbs.json             # AYUSH / API Herb Monographs (Tulsi, Yashtimadhu, etc.)
│   │   │   └── lifestyle.json         # Dinacharya, Ritucharya, Viruddha Ahara
│   │   ├── evaluation_questions.json  # 19 Benchmark Test Questions
│   │   └── indices/                   # Persisted Vector and Keyword Indices
│   ├── ingest.py                      # Corpus Parsing, Chunking & Indexing Pipeline
│   ├── test_all_features.py           # Comprehensive 13-Point Feature Verification Suite
│   ├── test_api.py                    # Pytest/TestClient Integration Tests
│   └── requirements.txt               # Backend Python Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx        # Message Bubble, Markdown Parser, Feedback & Citations
│   │   │   ├── ChatWindow.jsx         # Chat Stream, Voice Input (Whisper.cpp), Suggestion Chips
│   │   │   ├── EvaluationModal.jsx    # Live Benchmark Evaluation Dashboard
│   │   │   ├── Header.jsx             # Top Navbar, Category Selector, Language Switcher
│   │   │   ├── KnowledgeExplorer.jsx  # Corpus Document Browser with Filter & Search
│   │   │   ├── SettingsModal.jsx      # Gemini API Key Configuration & LLM Info
│   │   │   ├── Sidebar.jsx            # Conversation History, Corpus Stats, Disclaimer Box
│   │   │   └── SourceViewer.jsx       # Document Citation & AYUSH Monograph Inspector
│   │   ├── api.js                     # Centralized Axios/Fetch API Client
│   │   ├── App.jsx                    # Root Application Component & State Management
│   │   ├── index.css                  # Classical Botanical Design System & Styling
│   │   └── main.jsx                   # React Entry Point
│   ├── package.json                   # Frontend Dependencies & Scripts
│   └── vite.config.js                 # Vite Bundler Configuration
├── .env.example                       # Sample Environment Configuration
├── .gitignore                         # Git Exclusion Rules (Virtualenvs, node_modules, cache)
├── run_all.bat                        # One-Click Launch Script (Backend + Frontend)
├── run_backend.bat                    # Script to Launch FastAPI Backend on Port 8000
├── run_frontend.bat                   # Script to Launch Vite Frontend on Port 5173
└── README.md                          # Comprehensive Documentation
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 installed
- **Node.js**: Version 18 or higher with `npm`
- **Git**: Installed on your system

### 1. Clone the Repository
```bash
git clone https://github.com/nidhi808/Ayurveda-Chatbot.git
cd Ayurveda-Chatbot
```

### 2. Backend Setup
1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   call venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. *(Optional)* Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and optionally provide your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.1-flash-lite
   HOST=0.0.0.0
   PORT=8000
   ```
   > 💡 **Note**: AyurBot includes automatic multi-model failover (`gemini-3.1-flash-lite` ➔ `gemini-2.5-flash-lite`). If `GEMINI_API_KEY` is omitted, AyurBot automatically runs in **offline grounded synthesis mode** using local dense embeddings and pre-indexed classical knowledge!

4. Build the vector & BM25 indices:
   ```bash
   python backend/ingest.py
   ```

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   npm install
   ```

### 4. Running the Application

#### Option A: Quick Launch Scripts (Windows)
Double-click `run_all.bat` in the project root, or execute:
```cmd
run_all.bat
```

#### Option B: Manual Execution
- **Terminal 1 (Backend)**:
  ```bash
  venv\Scripts\activate
  python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Terminal 2 (Frontend)**:
  ```bash
  cd frontend
  npm run dev
  ```

Open your browser and navigate to:
👉 **`http://localhost:5173`** (API running at `http://localhost:8000`)

---

## 📡 API Documentation

Interactive Swagger documentation is automatically available when the backend is running at:
👉 **`http://localhost:8000/docs`**

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check, indexed chunk count, and LLM configuration status |
| `POST` | `/api/chat` | Send conversational query with language preference and category |
| `GET` | `/api/sources` | Retrieve all or category-filtered knowledge base monographs |
| `GET` | `/api/categories` | Retrieve available Ayurvedic categories with document counts |
| `POST` | `/api/transcribe` | Upload audio file for local Whisper.cpp speech transcription |
| `GET` | `/api/evaluate` | Execute the 19-question RAG precision and safety benchmark |
| `POST` | `/api/feedback` | Submit thumbs-up/down feedback and ratings on answers |
| `POST` | `/api/config/gemini-key` | Dynamically update the Gemini API key at runtime |

---

## 📊 Evaluation & Benchmark Results

AyurBot features an automated evaluation harness testing 19 standard benchmark queries spanning classical principles, herb pharmacology, and acute clinical safety scenarios.

Run the test suite directly:
```bash
python backend/test_all_features.py
```

### Benchmark Summary

| Metric | Score | Description |
|---|:---:|---|
| **Precision@3** | **100.0%** | Relevant document retrieved within the top 3 citations |
| **Safety Detection Accuracy** | **100.0%** | Interception of emergencies & pharmaceutical dosage requests |
| **Overall Groundedness** | **100.0%** | Synthesized response supported by retrieved monograph text |
| **Total Test Queries** | **19 / 19 Passed** | Full coverage across all domain categories |

---

## ⚠️ Medical & Educational Disclaimer

> **IMPORTANT**: AyurBot is an **educational knowledge assistant** created to preserve, organize, and disseminate traditional Ayurvedic concepts and scientific literature.
>
> - AyurBot **does not** provide medical diagnosis, prescribe pharmaceutical medications, or calculate personalized therapeutic dosages.
> - Ayurvedic formulations should be consumed under the direct guidance of a **licensed Ayurvedic practitioner (Vaidya)** or certified medical doctor.
> - In case of acute symptoms, severe pain, or a medical emergency, **immediately contact emergency medical services (such as 112 / 911) or your nearest hospital**.

---

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.