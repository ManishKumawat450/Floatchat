# 🌊 FloatChat
### AI-Powered Conversational Interface for ARGO Ocean Data Discovery and Visualization

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.3-blue)](https://postgresql.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-green)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)](https://chromadb.com)

> Built for **INCOIS (Indian National Centre for Ocean Information Services)** under **Ministry of Earth Sciences, Government of India**

---

## 📌 Problem Statement

Oceanographic data is vast, complex, and heterogeneous. The Argo program deploys autonomous profiling floats across the world's oceans generating extensive datasets in NetCDF format. Accessing this data requires domain knowledge and technical skills — creating barriers for non-technical users.

**FloatChat bridges this gap** by enabling natural language access to Indian Ocean Argo data.

---

## 🎯 What Can You Ask?

```
"What is the average temperature in Arabian Sea in 2023?"
"Show salinity profiles near equator in January 2024"
"How many floats are in the Indian Ocean?"
"Show float locations in Arabian Sea on 01-03-2026"
"Show temperature data in Bay of Bengal in 2024"
```

---

## 🏗️ System Architecture

```
User Query (Natural Language)
         ↓
  Streamlit Frontend
         ↓
  Auto Fetch (if new date)
         ↓
  ChromaDB RAG Pipeline
  (Ocean knowledge context)
         ↓
  Groq LLM (LLaMA 3.3-70B)
  (NL → SQL generation)
         ↓
  PostgreSQL Database
  (3M+ ocean records)
         ↓
  Answer + Visualization
  (Maps, Graphs, Metrics)
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data Source | Argo GDAC (IFREMER) | NetCDF ocean data download |
| Data Processing | Python, xarray, numpy | NetCDF parsing |
| Relational DB | PostgreSQL 18 | Structured data storage |
| Vector DB | ChromaDB | Semantic search + RAG |
| Embeddings | sentence-transformers | Text embeddings |
| LLM | Groq API (LLaMA 3.3-70B) | NL to SQL generation |
| Frontend | Streamlit | Chat UI + Dashboard |
| Visualization | Plotly | Maps + Graphs |

---

## 📁 Project Structure

```
FloatChat/
├── data/
│   ├── argo_cache/              ← Downloaded NetCDF files
│   └── processed_dates.txt      ← Tracks ingested dates
├── backend/
│   ├── fetcher.py               ← Realtime data download
│   ├── ingest.py                ← NetCDF → PostgreSQL
│   ├── sql_generator.py         ← NL to SQL (Groq LLM)
│   └── rag.py                   ← ChromaDB RAG pipeline
├── frontend/
│   └── app.py                   ← Streamlit dashboard
├── models/
│   └── vector_store/            ← ChromaDB storage
├── database/
│   └── schema.sql               ← PostgreSQL schema
├── .env                         ← Environment variables
├── requirements.txt             ← Dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/FloatChat.git
cd FloatChat
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create `.env` file:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=floatchat
DB_USER=postgres
DB_PASSWORD=your_password
GROQ_API_KEY=your_groq_api_key
```

### 5. Setup PostgreSQL Database
```bash
psql -U postgres -c "CREATE DATABASE floatchat;"
psql -U postgres -d floatchat -f database/schema.sql
```

### 6. Download Sample Data
```bash
python backend/fetcher.py
```

### 7. Ingest Data into DB
```bash
python backend/ingest.py
```

### 8. Initialize RAG System
```bash
python backend/rag.py
```

### 9. Run Application
```bash
streamlit run frontend/app.py
```

---

## 📊 Database Statistics

| Metric | Value |
|--------|-------|
| Total Records | 3,038,710+ |
| Unique Argo Floats | 265 |
| Date Range | 2021 – 2026 (Realtime) |
| Region | Indian Ocean (0-26°N, 55-101°E) |
| Data Source | Argo GDAC — IFREMER |

---

## 🧠 NLP Pipeline

FloatChat uses NLP at 4 stages:

1. **Intent Detection** — Understanding what user wants
2. **Entity Extraction** — Location, date, parameter extraction
3. **NL to SQL** — Converting query to PostgreSQL SQL
4. **Response Generation** — Human-friendly answer from DB results

### RAG Enhancement
- ChromaDB stores 15 ocean knowledge documents
- Covers Arabian Sea, Bay of Bengal, Indian Ocean facts
- Context retrieved before SQL generation for better accuracy

---

## 🗺️ Indian Ocean Coverage

```
Arabian Sea    : latitude  8-26°N, longitude  55-78°E
Bay of Bengal  : latitude  5-22°N, longitude  80-101°E
Indian Ocean   : latitude  0-26°N, longitude  55-101°E
```

---

## 📈 Features

- ✅ **Natural Language Chat** — Ask questions in plain English
- ✅ **Realtime Data** — Auto-downloads latest Argo data
- ✅ **Interactive Maps** — Plotly geospatial float locations
- ✅ **Temperature Graphs** — Time series visualization
- ✅ **Salinity Plots** — Scatter plot visualization
- ✅ **Depth Profiles** — Temperature vs Depth charts
- ✅ **Smart Caching** — No duplicate downloads/ingestion
- ✅ **RAG Pipeline** — Context-aware SQL generation
- ✅ **DB Stats** — Live database statistics in sidebar

---

## 📚 Research Papers

| Paper | Authors | Year | Link |
|-------|---------|------|------|
| OceanAI: Conversational Oceanographic Platform | Bowen Chen et al. | 2025 | [arxiv](https://arxiv.org/abs/2511.01019) |
| Agentic RAG Survey | Singh et al. | 2025 | [arxiv](https://arxiv.org/abs/2501.09136) |
| Text-to-SQL in LLM Era (IEEE TKDE) | Liu et al. | 2025 | [arxiv](https://arxiv.org/abs/2408.05109) |
| Geo-OLM: Earth Observation with LLMs | Multiple | 2025 | [arxiv](https://arxiv.org/abs/2504.04319) |
| Enhancing RAG: Best Practices | Li et al. | 2025 | [arxiv](https://arxiv.org/abs/2501.07391) |

---

## 🔑 API Keys Required

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Groq API](https://console.groq.com) | LLM for NL to SQL | Yes — Generous |

---

## 🏆 Organization

- **Organization**: Ministry of Earth Sciences (MoES)
- **Department**: INCOIS — Indian National Centre for Ocean Information Services
- **Data Source**: Argo Global Data Repository (IFREMER GDAC)
- **Indian Argo**: https://incois.gov.in/OON/index.jsp

---

## 📄 License

This project is developed for the Smart India Hackathon 2025 under Problem Statement by INCOIS, Ministry of Earth Sciences, Government of India.

---

*Built with ❤️ for Indian Ocean Science*
