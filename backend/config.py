from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "ExplainAI Video Engine"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "explainai"

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_root: str = "storage"

    # ── OpenAI / LLM ─────────────────────────────────────────────────────────
    openai_api_key: str = ""                      # set in .env
    openai_base_url: str = ""                     # override for Ollama, Together, etc.
    openai_model: str = "gpt-4o-mini"             # default model

    # ── TTS ───────────────────────────────────────────────────────────────────
    tts_model: str = "tts_models/en/ljspeech/tacotron2-DDC"

    # ── FFmpeg ───────────────────────────────────────────────────────────────────
    ffmpeg_path: str = ""   # leave empty to use system PATH


settings = Settings()
