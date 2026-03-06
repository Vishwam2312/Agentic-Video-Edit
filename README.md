# ExplainAI Video Engine

A FastAPI backend that converts research-paper PDFs into narrated explainer videos through a multi-agent AI pipeline:

**PDF Upload → Text Extraction → AI Script → Scene Planning → Manim Animation → FFmpeg Export → Final MP4**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Server](#running-the-server)
7. [Complete API Reference](#complete-api-reference)
   - [System Routes](#system-routes)
   - [Upload](#upload)
   - [Projects](#projects)
   - [Scripts](#scripts)
   - [Render Pipeline](#render-pipeline)
   - [Export (Legacy)](#export-legacy)
8. [Data Flow Walkthrough](#data-flow-walkthrough)
9. [MongoDB Collections](#mongodb-collections)
10. [Storage Layout](#storage-layout)
11. [AI Agents](#ai-agents)
12. [Services Layer](#services-layer)
13. [Repository Layer](#repository-layer)
14. [Models & Schemas](#models--schemas)
15. [Error Handling](#error-handling)
16. [Development Notes](#development-notes)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI App                        │
│              127.0.0.1:8000                          │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ /upload  │  │/projects │  │    /scripts       │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │             │                  │            │
│  ┌────▼─────────────▼──────────────────▼─────────┐  │
│  │             MongoDB (motor async)              │  │
│  │  collections: projects, scripts, scenes,       │  │
│  │               documents, videos, highlights    │  │
│  └────────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────── /render ────────────────────┐  │
│  │  1. ScriptRepository.get_script()               │  │
│  │  2. scene_agent.generate_scenes()   [LLM]       │  │
│  │  3. animation_agent.generate_code() [LLM]       │  │
│  │  4. animation_renderer.render_scene() [Manim]   │  │
│  │  5. ffmpeg concat  [FFmpeg]                     │  │
│  │  6. → storage/final/<video>.mp4                 │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Library / Tool | Version |
|-----------|---------------|---------|
| Web framework | FastAPI | 0.115.0 |
| ASGI server | Uvicorn | 0.30.6 |
| Data validation | Pydantic v2 | 2.8.2 |
| Config management | pydantic-settings | 2.4.0 |
| Async MongoDB | Motor | 3.5.1 |
| PDF extraction | PyMuPDF (fitz) | 1.24.9 |
| LLM client | OpenAI SDK | ≥1.40.0 |
| Animation render | Manim Community | latest |
| Video concat | FFmpeg | system |
| Logging | Loguru | 0.7.2 |

---

## Project Structure

```
Fast Api/
├── backend/
│   ├── main.py                  # App factory, lifespan, CORS, router mounts
│   ├── config.py                # Settings (pydantic-settings, reads from .env)
│   ├── agents/
│   │   ├── scene_agent.py       # LLM: script dict → list[SceneItem]
│   │   ├── animation_agent.py   # LLM: SceneItem → Manim Python code
│   │   ├── script_agent.py      # LLM: PDF text → structured script
│   │   ├── highlight_agent.py   # (reserved) highlight detection
│   │   ├── tts_agent.py         # (reserved) text-to-speech
│   │   └── sync_agent.py        # (reserved) audio-video sync
│   ├── models/
│   │   ├── base.py              # MongoBaseModel, PyObjectId
│   │   ├── document.py          # ParsedDocumentDocument, UploadResponse
│   │   ├── script.py            # ScriptDocument, ScriptStatus enum
│   │   ├── scene.py             # Scene model (legacy)
│   │   ├── schemas.py           # SubSceneCreate, SceneCreate, SceneOut
│   │   ├── video.py             # VideoDocument, VideoStatus enum
│   │   ├── project.py           # ProjectDocument
│   │   └── highlight.py         # Highlight model
│   ├── routers/
│   │   ├── __init__.py          # Re-exports all routers
│   │   ├── upload.py            # POST /upload/
│   │   ├── project_router.py    # CRUD /projects/
│   │   ├── script_router.py     # CRUD /scripts/
│   │   ├── render_pipeline.py   # POST /render/ (full pipeline)
│   │   └── export.py            # Legacy assemble/download endpoints
│   ├── services/
│   │   ├── database.py          # Motor client, get_database(), db_dependency()
│   │   ├── repositories.py      # BaseRepository + Project/Script/SceneRepository
│   │   ├── pdf_parser.py        # PyMuPDF extraction → ParseResult
│   │   ├── animation_renderer.py# Manim CLI wrapper → RenderResult
│   │   ├── video_exporter.py    # FFmpeg concat helper
│   │   ├── document_service.py  # Document CRUD helpers
│   │   ├── project_service.py   # Project CRUD helpers
│   │   ├── scene_service.py     # Scene CRUD helpers
│   │   ├── script_service.py    # Script CRUD helpers
│   │   └── video_service.py     # Video CRUD helpers
│   └── utils/
│       ├── errors.py            # raise_not_found(), validate_object_id()
│       └── file_utils.py        # save_upload_file()
├── storage/                     # Auto-created on first run
│   ├── uploads/                 # Uploaded PDFs
│   ├── scripts/                 # (reserved)
│   ├── scenes/                  # (reserved)
│   ├── animations/              # (reserved)
│   ├── audio/                   # (reserved)
│   ├── videos/                  # Manim-rendered MP4 chunks
│   └── final/                   # Final concatenated MP4s
├── .env                         # Local config (copy from .env.example)
├── .env.example                 # Template
├── requirements.txt
└── README.md
```

---

## Prerequisites

Install all of the following before running the project.

### 1. Python 3.12

```bash
python --version   # must be 3.12.x
```

### 2. MongoDB (local or Atlas)

- Default: `mongodb://localhost:27017`
- Database name: `explainai`
- Install MongoDB Community Edition or use Docker:
  ```bash
  docker run -d -p 27017:27017 --name mongo mongo:7
  ```

### 3. FFmpeg

Required for video concatenation.

- **Windows:** Download from https://ffmpeg.org/download.html, add to PATH, or set `FFMPEG_PATH` in `.env`
- Verify: `ffmpeg -version`

### 4. Manim Community Edition

Installed via pip (included in `requirements.txt`), but requires additional system dependencies:

- **Windows:** Install Cairo, Pango, and LaTeX (MiKTeX or TeX Live)
- Verify after install: `manim --version`
- Full setup guide: https://docs.manim.community/en/stable/installation.html

### 5. OpenAI-compatible LLM API

- Works with: OpenAI, Azure OpenAI, Ollama, Together AI, Groq, or any OpenAI-compatible endpoint
- Minimum model capability: instruction following + structured JSON output (GPT-4o-mini class)

---

## Installation

```bash
# 1. Open the project folder
cd "C:\Users\Lenovo\Desktop\Fast Api"

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 5. Edit .env with your values (see Configuration section below)
```

---

## Configuration

All configuration lives in `backend/config.py` (loaded via `pydantic-settings` from `.env`).

### `.env` File

```dotenv
# ── App ──────────────────────────────────────────────────────────────────────
APP_NAME="ExplainAI Video Engine"
APP_VERSION="0.1.0"
DEBUG=false

# ── CORS — add your frontend origin here ────────────────────────────────────
ALLOWED_ORIGINS='["http://localhost:3000", "http://localhost:5173"]'

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=explainai

# ── File storage root (relative to where you run uvicorn) ───────────────────
STORAGE_ROOT=storage

# ── LLM API ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=                 # Leave empty for OpenAI; set for Ollama/Together/etc.
OPENAI_MODEL=gpt-4o-mini         # Any model supported by your endpoint

# ── TTS (reserved — not yet active) ─────────────────────────────────────────
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC

# ── FFmpeg path (leave empty if ffmpeg is on PATH) ──────────────────────────
FFMPEG_PATH=
```

### Settings Reference

| Key | Default | Description |
|-----|---------|-------------|
| `APP_NAME` | `ExplainAI Video Engine` | Shown in API root response |
| `APP_VERSION` | `0.1.0` | Shown in API root response |
| `DEBUG` | `false` | Enables extra logging |
| `ALLOWED_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | CORS whitelist |
| `MONGO_URI` | `mongodb://localhost:27017` | Motor connection string |
| `DATABASE_NAME` | `explainai` | MongoDB database name |
| `STORAGE_ROOT` | `storage` | Root for all file storage |
| `OPENAI_API_KEY` | *(required)* | LLM API key |
| `OPENAI_BASE_URL` | *(empty = OpenAI)* | Override for compatible endpoints |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model identifier |
| `FFMPEG_PATH` | *(empty = PATH)* | Explicit path to ffmpeg binary |

### Using a Local LLM (e.g. Ollama)

```dotenv
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama        # any non-empty string
OPENAI_MODEL=llama3.2
```

---

## Running the Server

```bash
# Activate venv first
venv\Scripts\activate

# From the "Fast Api" directory:
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000` | API base URL |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc documentation |
| `http://127.0.0.1:8000/openapi.json` | Raw OpenAPI schema |

---

## Complete API Reference

All paths are relative to `http://127.0.0.1:8000`.

---

### System Routes

#### `GET /`

Returns basic API info. No authentication required.

**Response `200`:**
```json
{
  "name": "ExplainAI Video Engine",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

---

#### `GET /health`

Liveness probe for health checks.

**Response `200`:**
```json
{ "status": "ok" }
```

---

### Upload

#### `POST /api/v1/upload/`

Upload a research paper PDF. Creates a **Project** and a **ParsedDocument** automatically.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Human-readable project/paper title |
| `description` | string | No | Optional description |
| `file` | file (PDF) | Yes | The PDF file to upload |

**Response `200`:**
```json
{
  "document_id": "66a1b2c3d4e5f6a7b8c9d0e1",
  "project_id":  "66a1b2c3d4e5f6a7b8c9d0e2",
  "file_path": "storage/uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "original_filename": "attention_is_all_you_need.pdf",
  "page_count": 15,
  "text_length": 47823,
  "word_count": 7843,
  "pdf_title": "Attention Is All You Need",
  "pdf_author": "Vaswani et al."
}
```

**What happens internally:**
1. PDF is saved to `storage/uploads/<uuid>.pdf`
2. A new `Project` document is created in MongoDB
3. PyMuPDF extracts all text and metadata from the PDF
4. A `ParsedDocument` is created in MongoDB linked to the project
5. The project is updated with the `document_id`

> `POST /api/v1/upload/paper` is an alias for this endpoint (hidden from Swagger).

---

### Projects

#### `POST /api/v1/projects/`

Create a new project manually (without uploading a PDF).

**Request body:**
```json
{
  "title": "My Research Project",
  "description": "Optional description"
}
```

**Response `201`:**
```json
{
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "title": "My Research Project",
  "description": "Optional description",
  "created_at": "2024-07-25T10:30:00Z"
}
```

---

#### `GET /api/v1/projects/`

List all projects with pagination.

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `skip` | int | `0` | Records to skip |
| `limit` | int | `20` | Max records to return |

**Response `200`:** Array of project objects.

---

#### `GET /api/v1/projects/{project_id}`

Get a single project by its `project_id` string.

**Response `200`:** Project object.  
**Response `404`:** Project not found.

---

#### `PUT /api/v1/projects/{project_id}`

Full update of a project.

**Request body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response `200`:** Updated project object.  
**Response `404`:** Project not found.

---

#### `DELETE /api/v1/projects/{project_id}`

**Response `204`:** No content.  
**Response `404`:** Project not found.

---

### Scripts

A "script" is the narration text that feeds the render pipeline. Create it manually or eventually via the script generation agent.

#### `POST /api/v1/scripts/`

**Request body:**
```json
{
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "title": "Attention Mechanism Explainer",
  "content": "In this video, we explore how attention mechanisms work..."
}
```

**Response `201`:**
```json
{
  "script_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "title": "Attention Mechanism Explainer",
  "content": "In this video, we explore how attention mechanisms work...",
  "created_at": "2024-07-25T10:35:00Z"
}
```

> **Important:** `script_id` is a **UUID string**, not a MongoDB ObjectId. Use this value when calling `POST /api/v1/render/`.

---

#### `GET /api/v1/scripts/`

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `project_id` | string | — | Filter by project (optional) |
| `skip` | int | `0` | Pagination offset |
| `limit` | int | `20` | Max records |

**Response `200`:** Array of script objects.

---

#### `GET /api/v1/scripts/{script_id}`

**Response `200`:** Script object.  
**Response `404`:** Not found.

---

#### `PUT /api/v1/scripts/{script_id}`

**Request body:**
```json
{
  "title": "New title",
  "content": "Updated narration text..."
}
```

**Response `200`:** Updated script object.

---

#### `DELETE /api/v1/scripts/{script_id}`

**Response `204`:** No content.

---

### Render Pipeline

The main endpoint — runs the complete end-to-end pipeline.

#### `POST /api/v1/render/`

Generates scenes via LLM, creates Manim animations, renders MP4 chunks, and concatenates them into one final video.

**Request body:**
```json
{
  "script_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `script_id` | string (UUID) | Yes | UUID of a script from `POST /api/v1/scripts/` |

**Response `200`:**
```json
{
  "video_url": "/storage/final/render_a1b2c3d4_7f3a91bc.mp4",
  "scene_count": 5,
  "chunk_count": 14
}
```

| Field | Description |
|-------|-------------|
| `video_url` | Relative path to the output MP4 |
| `scene_count` | Number of top-level scenes generated |
| `chunk_count` | Total rendered video chunks (1 per subscene) |

**Error responses:**

| HTTP | Cause |
|------|-------|
| `404` | Script not found |
| `422` | Pipeline produced no video chunks |
| `502` | LLM call failed, Manim render failed, or FFmpeg concat failed |

**Pipeline steps:**

```
1. ScriptRepository.get_script(db, script_id)
       ↓  script document
2. scene_agent.generate_scenes(script_payload)
       ↓  list[SceneItem]  (3–8 scenes, 2–4 subscenes each)
3. For each subscene:
   a. animation_agent.generate_animation_code({text, visual_description, index})
          ↓  Manim Python code string
   b. animation_renderer.render_scene(manim_code, stem="scene1_sub1")
          ↓  RenderResult{video_id, path}
          → file saved: storage/videos/scene1_sub1.mp4
4. _ffmpeg_concat(all_chunks, final_path)
       → file saved: storage/final/render_<id>_<rand>.mp4
5. Return RenderResponse
```

> **Warning:** This is a long-running request. Rendering multiple Manim scenes can take several minutes. Consider running it as a background job in production.

---

### Export (Legacy)

These endpoints support the older assemble-from-database workflow, where video chunk IDs are stored in scene documents and assembled on demand. Still mounted at `/api/v1/render/`.

#### `POST /api/v1/render/export-video`

Assemble a final video from scenes stored in MongoDB.

**Request body:**
```json
{
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "output_stem": "my_video_name"
}
```

**Response `201`:**
```json
{
  "video_id": "66a1b2c3d4e5f6a7b8c9d0e9",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "output_path": "storage/final/my_video_name.mp4",
  "file_size_bytes": 18234567,
  "scene_count": 0,
  "status": "ready"
}
```

---

#### `POST /api/v1/render/assemble/{project_id}`

Mark a project's video document as `assembling` (status management only — does not run FFmpeg).

**Response `200`:** `VideoDocument` with `status: "assembling"`.

---

#### `GET /api/v1/render/project/{project_id}`

Get video export status for a project.

**Response `200`:**
```json
{
  "id": "66a1b2c3d4e5f6a7b8c9d0e9",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "status": "ready",
  "output_path": "storage/final/project_66a1b2c3_final.mp4",
  "file_size_bytes": 18234567,
  "scene_count": 5
}
```

**Status values:** `pending` | `assembling` | `ready` | `failed`

---

#### `GET /api/v1/render/download/{video_id}`

Stream the final MP4 file by MongoDB video `_id`.

**Response `200`:** Binary MP4 (`Content-Type: video/mp4`)  
**Response `404`:** Video record or file not found.

---

#### `GET /api/v1/render/{video_id}`

Get a video document by MongoDB ObjectId.

**Response `200`:** `VideoDocument` JSON.  
**Response `404`:** Not found.

---

## Data Flow Walkthrough

Recommended end-to-end flow from the frontend:

```
Step 1 — Upload PDF
  POST /api/v1/upload/
  ← { project_id, document_id, page_count, ... }
  Store: project_id

Step 2 — Create Script
  POST /api/v1/scripts/
  body: { project_id, title, content }
  ← { script_id, ... }
  Store: script_id  ← this is a UUID, not an ObjectId

Step 3 — Run Render Pipeline
  POST /api/v1/render/
  body: { script_id }
  ← { video_url, scene_count, chunk_count }
  (long-running — can take several minutes)

Step 4 — Serve the Video
  GET <API_BASE_URL><video_url>
  e.g. http://127.0.0.1:8000/storage/final/render_xxx.mp4
```

### Frontend Integration Checklist

- [ ] Store `project_id` (ObjectId hex string, 24 chars) after upload or project creation
- [ ] Store `script_id` (UUID string, 36 chars with dashes) after script creation — **not** interchangeable with MongoDB `_id`
- [ ] `POST /render/` blocks until completion; for production, wrap it in a background job and poll status
- [ ] `video_url` is a relative path. Prefix with API base URL or mount `storage/` as static files (see Development Notes)
- [ ] CORS is pre-configured for `localhost:3000` and `localhost:5173`. Add your production domain to `ALLOWED_ORIGINS` in `.env`

---

## MongoDB Collections

All timestamps are UTC ISO-8601. `_id` is a MongoDB ObjectId serialized as a 24-char hex string.

### `projects`

```json
{
  "_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "project_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "My Research Project",
  "description": "Optional description",
  "created_at": "2024-07-25T10:30:00Z",
  "updated_at": "2024-07-25T10:30:00Z"
}
```

### `documents`

```json
{
  "_id": "66a1b2c3d4e5f6a7b8c9d0e1",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "original_filename": "paper.pdf",
  "upload_path": "storage/uploads/<uuid>.pdf",
  "text": "Full extracted plain-text...",
  "text_length": 47823,
  "page_count": 15,
  "word_count": 7843,
  "pdf_title": "Attention Is All You Need",
  "pdf_author": "Vaswani et al.",
  "pdf_subject": null,
  "pdf_producer": "LaTeX",
  "created_at": "2024-07-25T10:30:05Z",
  "updated_at": "2024-07-25T10:30:05Z"
}
```

### `scripts`

```json
{
  "_id": "66a1b2c3d4e5f6a7b8c9d0e3",
  "script_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "title": "Attention Mechanism Explainer",
  "content": "In this video, we explore...",
  "status": "ready",
  "sections": [{ "heading": "Introduction", "text": "..." }],
  "word_count": 512,
  "estimated_duration_s": 180.0,
  "model_used": "gpt-4o-mini",
  "created_at": "2024-07-25T10:35:00Z",
  "updated_at": "2024-07-25T10:35:00Z"
}
```

**Script status values:** `pending` | `generating` | `ready` | `failed`

### `scenes`

```json
{
  "_id": "66a1b2c3d4e5f6a7b8c9d0e4",
  "scene_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "scene_title": "Introduction to Attention",
  "subscenes": [
    {
      "subscene_id": "c3d4e5f6a7b890",
      "text": "Attention mechanisms allow models to focus...",
      "visual_description": "Animated diagram showing query-key-value",
      "video_ids": ["scene1_sub1", "scene1_sub2"],
      "metadata": {}
    }
  ],
  "created_at": "2024-07-25T10:40:00Z",
  "updated_at": "2024-07-25T10:40:00Z"
}
```

### `videos`

```json
{
  "_id": "66a1b2c3d4e5f6a7b8c9d0e9",
  "project_id": "66a1b2c3d4e5f6a7b8c9d0e2",
  "status": "ready",
  "scene_count": 5,
  "output_path": "storage/final/project_66a1b2c3_final.mp4",
  "file_size_bytes": 18234567,
  "resolution": null,
  "fps": null,
  "created_at": "2024-07-25T11:00:00Z",
  "updated_at": "2024-07-25T11:05:00Z"
}
```

**Video status values:** `pending` | `assembling` | `ready` | `failed`

---

## Storage Layout

```
storage/
├── uploads/          ← Raw uploaded PDFs
│   └── <uuid>.pdf
├── scripts/          ← Reserved for script exports
├── scenes/           ← Reserved for scene assets
├── animations/       ← Reserved for animation source
├── audio/            ← Reserved for TTS audio
├── videos/           ← Manim-rendered MP4 chunks (one per subscene)
│   └── scene1_sub1.mp4
└── final/            ← Final concatenated output videos
    └── render_a1b2c3d4_7f3a91bc.mp4
```

All subdirectories are created automatically on startup.

---

## AI Agents

### `scene_agent.generate_scenes(script, *, model=None)`

Converts a script dict into a hierarchy of scenes and subscenes.

**Input:**
```python
{
    "title": "Video Title",
    "sections": [
        {"heading": "Introduction", "text": "Full narration text..."}
    ]
}
```

**Output:** `list[SceneItem]`
```python
@dataclass
class SubSceneItem:
    text: str                   # narration for this subscene
    visual_description: str     # what to animate

@dataclass
class SceneItem:
    scene_title: str
    subscenes: list[SubSceneItem]
```

LLM guidelines: 3–8 scenes per script, 2–4 subscenes per scene.

---

### `animation_agent.generate_animation_code(scene, *, model=None)`

Converts a subscene dict into complete Manim Python source code.

**Input:**
```python
{
    "text": "Narration text for this subscene",
    "visual_description": "Description of what to animate",
    "index": 0
}
```

Also accepts legacy format with `narration_text` key instead of `text`.

**Output:** Complete Manim Python string containing a class `SceneAnimation(Scene)`.

Temperature is set to 0.2 for deterministic, reproducible output.

---

### `animation_renderer.render_scene(manim_code, *, stem, quality, timeout)`

Runs the Manim CLI in an isolated temp directory.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `manim_code` | — | Full Manim Python source |
| `stem` | UUID | Output filename stem |
| `quality` | `"l"` | `l`=480p15, `m`=720p30, `h`=1080p60 |
| `timeout` | `300` | Seconds before subprocess is killed |

**Returns:** `RenderResult(video_id=stem, path=Path("storage/videos/<stem>.mp4"))`

---

## Services Layer

### `database.py`

```python
await connect_db()     # called on startup (via main.py lifespan)
await disconnect_db()  # called on shutdown

db = get_database()    # → AsyncIOMotorDatabase

# FastAPI dependency:
async def route(db = Depends(db_dependency)): ...
```

**Collection name constants:**
```python
class Collections:
    PROJECTS   = "projects"
    SCRIPTS    = "scripts"
    SCENES     = "scenes"
    VIDEOS     = "videos"
    DOCUMENTS  = "documents"
    HIGHLIGHTS = "highlights"
```

---

### `pdf_parser.py`

```python
result = await parse_pdf(Path("storage/uploads/file.pdf"))
# ParseResult fields:
result.text          # Full plain text
result.text_length   # Character count
result.word_count    # Word count
result.page_count    # PDF page count
result.pdf_title     # From PDF metadata (or None)
result.pdf_author    # From PDF metadata (or None)
result.pages         # list[str] — per-page text
```

Runs PyMuPDF synchronously in a thread via `asyncio.to_thread`.

---

### `video_exporter.py`

```python
# Assemble all subscene chunks for one scene
path = await assemble_scene(scene_id, db=db, output_stem="my_scene")

# Concatenate all scene videos for a project
path = await export_final_video(project_id, db=db, output_stem="my_video")
```

---

## Repository Layer

`services/repositories.py` is the MongoDB access layer on top of Motor. All methods are `async classmethods`.

### `BaseRepository` — generic methods (all collections)

```python
# Create — auto-adds created_at, updated_at
doc = await BaseRepository.create(db, {"field": "value"})

# Get by MongoDB ObjectId string
doc = await BaseRepository.get_by_id(db, "66a1b2c3d4e5f6a7b8c9d0e2")

# List with optional filter + pagination
docs = await BaseRepository.get_all(
    db,
    filter={"status": "ready"},
    skip=0, limit=20,
    sort_field="created_at", sort_dir=-1,
)

# Update — uses $set, bumps updated_at
doc = await BaseRepository.update(db, "66a1....", {"title": "New Title"})

# Delete by ObjectId
deleted: bool = await BaseRepository.delete(db, "66a1....")
```

### `ScriptRepository` — keyed on `script_id` (UUID)

```python
doc  = await ScriptRepository.create_script(db, {
    "project_id": "...", "title": "...", "content": "..."
})
doc  = await ScriptRepository.get_script(db, script_id)
docs = await ScriptRepository.get_scripts_by_project(db, project_id, skip=0, limit=20)
doc  = await ScriptRepository.update_script(db, script_id, {"content": "..."})
ok   = await ScriptRepository.delete_script(db, script_id)
```

### `SceneRepository` — keyed on `scene_id` (UUID)

```python
doc  = await SceneRepository.create_scene(db, project_id, scene_title)
doc  = await SceneRepository.get_scene(db, scene_id)
docs = await SceneRepository.get_scenes_by_project(db, project_id, skip=0, limit=20)
doc  = await SceneRepository.update_scene(db, scene_id, {"scene_title": "..."})
ok   = await SceneRepository.delete_scene(db, scene_id)
```

### `ProjectRepository`

Inherits all 5 `BaseRepository` methods. Keyed on MongoDB `_id` (ObjectId).

---

## Models & Schemas

### `MongoBaseModel`

Base class for all MongoDB-backed models:

```python
class MongoBaseModel(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    created_at: datetime
    updated_at: datetime
```

`PyObjectId` validates that a string is a valid 24-hex MongoDB ObjectId. serializes `_id` as a plain string in JSON responses.

### ID Type Reference

| Collection | API key | Type | Example |
|------------|---------|------|---------|
| projects | `project_id` | UUID string | `550e8400-e29b-41d4-a716-446655440001` |
| scripts | `script_id` | UUID string | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| scenes | `scene_id` | UUID string | `b2c3d4e5-f6a7-8901-bcde-f12345678901` |
| documents | `document_id` / `_id` | ObjectId hex | `66a1b2c3d4e5f6a7b8c9d0e1` |
| videos | `video_id` / `_id` | ObjectId hex | `66a1b2c3d4e5f6a7b8c9d0e9` |

> The render pipeline (`POST /render/`) takes `script_id` (UUID), not `_id`.

---

## Error Handling

### Standard Error Shape

```json
{
  "detail": "Human-readable error message"
}
```

### Validation Error Shape (422)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "script_id"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### Common HTTP Error Codes

| Code | Cause |
|------|-------|
| `400` | Bad request |
| `404` | Resource not found |
| `422` | Validation error — missing fields, wrong types, or invalid ObjectId |
| `502` | Upstream failure — LLM API error, Manim crash, or FFmpeg failure |

---

## Development Notes

### Adding CORS Origins

```dotenv
ALLOWED_ORIGINS='["http://localhost:3000", "https://my-app.vercel.app"]'
```

### Serving Final Videos as Static Files

Add to `backend/main.py`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
```

Then videos are accessible at: `http://127.0.0.1:8000/storage/final/render_xxx.mp4`

### Long-Running Renders (Production)

`POST /api/v1/render/` can take 5–30 minutes. Recommended production pattern:
1. Accept request, return a `job_id` immediately
2. Run the pipeline in a background worker (Celery, ARQ, or FastAPI `BackgroundTasks`)
3. Expose `GET /api/v1/render/status/{job_id}` for polling
4. Notify frontend via WebSocket or Server-Sent Events when done

### Manim Quality Levels

| Flag | Resolution | FPS | Use case |
|------|-----------|-----|----------|
| `-ql` | 480p | 15 | Development / fast iteration |
| `-qm` | 720p | 30 | Preview |
| `-qh` | 1080p | 60 | Production |

Change the default in `services/animation_renderer.py` (`_DEFAULT_QUALITY`), or pass `quality` explicitly to `render_scene()`.

### Running Tests

```bash
pytest backend/ -v
```

Uses `httpx.AsyncClient` as the async test client with `pytest-asyncio`.

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
