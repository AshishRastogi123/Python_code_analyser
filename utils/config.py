"""
Configuration management for the code modernization platform.

Design Rationale:
- Centralized configuration from environment variables
- Sensible defaults for development and production
- Supports .env file loading (optional, no hard dependency)
- Clean separation of concerns (configuration is isolated)
- Easy to extend with YAML or other formats later without refactoring callers

Architecture Pattern:
- Config class provides read-only access to settings
- Environment variable precedence: env vars > .env file > defaults
- All paths are normalized to absolute paths
- Lazy initialization to avoid errors if not all env vars are set
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """
    Centralized configuration management using environment variables.
    """

    # Directories
    _BASE_DIR: Optional[Path] = None
    _CORE_DIR: Optional[Path] = None
    _RAG_DIR: Optional[Path] = None
    _UI_DIR: Optional[Path] = None

    @classmethod
    def initialize(cls, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).parent.parent

        cls._BASE_DIR = Path(base_dir).resolve()
        cls._CORE_DIR = cls._BASE_DIR / "core"
        cls._RAG_DIR = cls._BASE_DIR / "rag"
        cls._UI_DIR = cls._BASE_DIR / "ui"

    # ========== LOGGING CONFIGURATION ==========

    @classmethod
    def log_level(cls) -> str:
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def log_file(cls) -> Optional[str]:
        log_file = os.getenv("LOG_FILE")
        return str(Path(log_file).resolve()) if log_file else None

    # ========== FILE PATHS ==========

    @classmethod
    def base_dir(cls) -> Path:
        if cls._BASE_DIR is None:
            cls.initialize()
        return cls._BASE_DIR

    @classmethod
    def core_dir(cls) -> Path:
        if cls._CORE_DIR is None:
            cls.initialize()
        return cls._CORE_DIR

    @classmethod
    def rag_dir(cls) -> Path:
        if cls._RAG_DIR is None:
            cls.initialize()
        return cls._RAG_DIR

    @classmethod
    def ui_dir(cls) -> Path:
        if cls._UI_DIR is None:
            cls.initialize()
        return cls._UI_DIR

    # ========== RAG / EMBEDDING CONFIGURATION ==========

    @classmethod
    def embedding_model(cls) -> str:
        return os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    @classmethod
    def faiss_index_path(cls) -> Path:
        return Path(
            os.getenv(
                "FAISS_INDEX_PATH",
                cls.rag_dir() / "index.faiss"
            )
        ).resolve()

    @classmethod
    def chunks_cache_path(cls) -> Path:
        return Path(
            os.getenv(
                "CHUNKS_CACHE_PATH",
                cls.rag_dir() / "chunks.pkl"
            )
        ).resolve()

    # ========== ANALYSIS CONFIGURATION ==========

    @classmethod
    def max_file_size_mb(cls) -> int:
        try:
            return int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        except ValueError:
            return 10

    @classmethod
    def ignore_patterns(cls) -> list[str]:
        default = "__pycache__,.git,venv,env,.venv,.pytest_cache,.tox,*.egg-info,node_modules"
        return [p.strip() for p in os.getenv("IGNORE_PATTERNS", default).split(",")]

    # ========== LLM CONFIGURATION ==========

    @classmethod
    def llm_provider(cls) -> str:
        """
        Supported values:
        - groq
        - ollama
        - openai
        - dummy
        """
        return os.getenv("LLM_PROVIDER", "dummy").lower()

    @classmethod
    def groq_api_key(cls) -> Optional[str]:
        return os.getenv("GROQ_API_KEY")

    @classmethod
    def groq_model(cls) -> str:
        """
        Groq model to use.

        Default: llama-3.1-8b-instant (stable, fast, supported)
        """
        return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    @classmethod
    def openai_api_key(cls) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    @classmethod
    def openai_model(cls) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # ========== API CONFIGURATION ==========

    @classmethod
    def api_host(cls) -> str:
        return os.getenv("API_HOST", "localhost")

    @classmethod
    def api_port(cls) -> int:
        try:
            return int(os.getenv("API_PORT", "8000"))
        except ValueError:
            return 8000

    @classmethod
    def api_debug(cls) -> bool:
        return os.getenv("API_DEBUG", "false").lower() in ("true", "1", "yes")

    # ========== VALIDATION ==========

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        warnings = []

        if not cls.base_dir().exists():
            warnings.append(f"Base directory not found: {cls.base_dir()}")

        if not cls.faiss_index_path().exists():
            warnings.append(
                f"FAISS index not found: {cls.faiss_index_path()}\n"
                "Run: python analyzer.py <file> --command index"
            )

        if cls.llm_provider() == "groq" and not cls.groq_api_key():
            warnings.append(
                "LLM provider set to 'groq' but GROQ_API_KEY is not set\n"
                "Get key from: https://console.groq.com"
            )

        if cls.llm_provider() == "openai" and not cls.openai_api_key():
            warnings.append(
                "LLM provider set to 'openai' but OPENAI_API_KEY is not set"
            )

        return len(warnings) == 0, warnings
