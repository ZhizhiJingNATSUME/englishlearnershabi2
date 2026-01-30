# 📚 Faga Adaptive English Teacher

An AI-powered personalized English reading application that helps advanced learners improve their skills through adaptive content recommendation and deep LLM analysis.

![Clean Mode](https://via.placeholder.com/800x400?text=Clean+Reading+Mode)
*(Immersive reading experience without distractions)*

## ✨ Key Features

- **🧠 Smart Recommendation System**: Suggests articles based on your CEFR level calculation and interest profile.
- **📝 Dual-Mode Reader**:
    - **Clean Mode**: A distraction-free, beautifully typographed reading environment.
    - **Learning Mode**: One-click toggles deep analysis, highlighting key vocabulary, collocations, and sentence structures.
- **🤖 Deep AI Analysis**: Powered by **Gemini 2.5 Flash**, the system extracts:
    - **Vocabulary**: CEFR-target words with definitions.
    - **Collocations**: Native-like phrases and idioms.
    - **Sentence Patterns**: Advanced grammatical structures and rhetorical devices.
- **🌍 Multi-Source Import**: Automatically aggregates content from Wikipedia, VOA Learning English, and NewsAPI.
- **📊 Progress Tracking**: Tracks reading history, vocabulary bank, and learning statistics.

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: TailwindCSS (v4) + Typography Plugin
- **Markdown**: React Markdown for perfect rendering
- **Icons**: Lucide React

### Backend
- **Server**: Flask (Python)
- **Database**: SQLite + SQLAlchemy
- **AI/LLM**: Google Gemini API (gemini-2.5-flash)
- **Vectors**: FAISS + Sentence Transformers (for recommendation)
- **Pipeline**: Pydantic for structured data validation

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Recommended for python dependency management)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/faga-adaptive-english-teacher.git
cd faga-adaptive-english-teacher

# Setup Backend Environment
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY and NEWS_API_KEY
```

### 3. Initialize Data

You can populate the database with initial content using the pipeline:

```bash
# Fetch 5 articles from Wikipedia only (Testing)
uv run python -m backend.data_pipeline.pipeline --limit 5 --sources wikipedia
```

### 4. Create Test User (Optional)

If you need a ready-made account:

```bash
uv run python scripts/create_test_user.py
```
*Creates user: `test` / Password: `test`*

### 5. Run Application

Start both Backend and Frontend with a single command:

```bash
./start_all.sh
```
- **Backend API**: http://localhost:5000
- **Frontend App**: http://localhost:5173

## 📖 User Guide

### Reading Modes
- **Clean Mode**: Default view. Uses `ReactMarkdown` and `Tailwind Typography` to present a clean, book-like layout.
- **Learning Mode**: Click the "Learning" toggle in the header. The app will:
    - Highlight **Vocabulary** (Green)
    - Highlight **Collocations** (Orange)
    - Highlight **Sentence Patterns** (Blue)
    - Open a sidebar analysis panel when you click any highlight.

### Data Pipeline
The `pipeline.py` script manages data ingestion:
- **Fetch**: Crawls data from configured sources.
- **Clean**: Normalizes text and calculates stats (Word count, Readability).
- **Analyze**: Send content to Gemini LLM to extract learning points.
- **Store**: Saves structured data to SQLite.

## 📂 Project Structure

```
faga-adaptive-english-teacher/
├── backend/
│   ├── app.py                   # Flask API Entry
│   ├── models.py                # Database Schema
│   ├── recommender.py           # Recommendation Engine
│   └── data_pipeline/           # ETL & AI Analysis
│       ├── llm_analyzer.py      # Gemini Interface
│       └── pipeline.py          # Main Pipeline Script
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Reader.tsx       # Core Reading Component
│   │   ├── services/            # API Client
│   │   └── App.tsx              # Main Router & Logic
│   └── package.json             # Frontend Dependencies
├── scripts/
│   ├── create_test_user.py      # User Helper
│   └── reanalyze_article.py     # Debug Helper
└── start_all.sh                 # Startup Script
```

## 📝 Latest Updates

### v1.0.0 Refactor
- **Frontend Rewrite**: Moved from Vanilla JS to React/TypeScript for better state management.
- **Design System**: Adopted TailwindCSS for a modern, responsive UI.
- **LLM Upgrade**: Upgraded to `gemini-2.5-flash` with dynamic context window handling (6k tokens) and full-text analysis capabilities.
- **Pipeline Robustness**: Enhanced error handling and dynamic retry logic for data fetching.
