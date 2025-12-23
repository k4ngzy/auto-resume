# Resume Tailor

> An engineering system for stable and reproducible resume customization, leveraging offline job retrieval to guide resume rewriting with similar job description.

Resume Tailor is a resume optimization tool built on large language models and offline retrieval. The system retrieves target positions that are semantically similar to a user’s resume from a local job database, providing explicit job-context constraints for generation. It performs structured gap analysis between the resume and job requirements, generates position-specific optimization suggestions, and ultimately produces a polished, submission-ready PDF resume automatically.

By introducing a retrieval-augmented mechanism, the system supplies clear, user-aligned target constraints for resume rewriting. This effectively reduces uncontrolled expansion and semantic drift commonly seen when relying solely on prompts, avoiding large, unstable rewrites.

## ✨ Features

1. Retrieval-Augmented Generation (RAG) based on an offline job database
2. Structured gap analysis between resumes and job requirements
3. Reusable, position-specific resume generation workflow
4. Automated resume layout and PDF export

## ⚙️ Dependencies & Prerequisites

* Python 3.10+
* Recommended: `uv` for dependency management
* LaTeX (PDF export requires `xelatex`)
* Playwright browser (optional, only for offline data collection scripts)

## 🚀 Quick Start

```bash
# 1. Clone the repository and enter the directory
git clone https://github.com/k4ngzy/resume-tailor.git
cd resume-tailor

# 2. Install dependencies
uv sync

# 3. Configure environment variables
# Create a .env file in the project root with the following content:
# API_KEY=your_api_key
# BASE_URL=https://api.openai.com/v1/

# 4. Start the service (backend + frontend)
./start.sh
```

## 📦 Optional: Offline Job Data Collection & Index Building

```bash
# 1. Install Playwright browser (only for offline crawling)
uv run playwright install chromium

# 2. Collect job data and generate JSONL (example: Python roles)
uv run python tools/offline_job_crawl.py --jobs Python --max-count 50

# 3. Build the vector index
uv run python tools/build_job_index.py \
  --source-path backend/data/offline_jobs.jsonl \
  --db-path backend/chromadb_data \
  --collection offline_jobs \
  --device cpu \
  --allow-remote
```

## 📂 Project Structure

```
backend/          FastAPI main app, prompts, and tools; data dirs: data/, chromadb_data/
frontend/         Streamlit UI, forms, and module editors
llm/              LLM factory (OpenAI-compatible)
tools/            Text extraction, LaTeX compilation helpers, offline index building, optional crawlers
resume-template/  LaTeX templates and assets
docs/             Examples and debugging files
start.sh          One-click startup script
```

## ⚠️ Notes

* PDF export depends on `xelatex`; please install TeX Live / MacTeX first
