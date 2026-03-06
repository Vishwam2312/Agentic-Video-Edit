# ExplainAI Video Engine — Backend

> Hackathon project · FastAPI backend that orchestrates multiple AI agents to convert research papers into explainable videos.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| Server | Uvicorn (ASGI) |
| Language | Python 3.11 |
| Validation | Pydantic v2 |

---

## Project Structure

```
explainai-backend/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── routers/         # Route handlers (APIRouter modules)
│   ├── agents/          # AI agent orchestration logic
│   ├── services/        # Business logic & external integrations
│   ├── models/          # Pydantic schemas & domain models
│   └── utils/           # Shared helpers & constants
│
├── storage/
│   ├── uploads/         # Incoming research paper PDFs
│   ├── scripts/         # Generated narration scripts
│   ├── scenes/          # Scene breakdown JSON/data
│   ├── animations/      # Animation assets per scene
│   ├── audio/           # TTS-generated audio files
│   ├── videos/          # Per-scene rendered videos
│   └── final/           # Final assembled output videos
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup Instructions

### 1. Clone / initialise the repository

```bash
git init
git add .
git commit -m "chore: initial project scaffold"
```

### 2. Create & activate a Python 3.11 virtual environment

**Windows (PowerShell)**
```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

> `.env` is git-ignored. Never commit secrets.

### 5. Run the development server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- Swagger UI → http://localhost:8000/docs
- ReDoc      → http://localhost:8000/redoc
- Health     → http://localhost:8000/health

---

## Running Tests

```bash
pytest
```

---

## Contributing

1. Create a feature branch: `git checkout -b feature/<name>`
2. Make changes and run tests
3. Open a pull request

---

*Built for a hackathon — ExplainAI Video Engine · 2026*
