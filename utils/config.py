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
import json


class Config:
    """
    Centralized configuration management using environment variables.
    
    Provides sensible defaults and supports override via:
    1. Environment variables (highest priority)
    2. .env file (if present)
    3. Built-in defaults (lowest priority)
    
    All file paths are normalized to absolute paths.
    """
    
    # Directories
    _BASE_DIR: Optional[Path] = None
    _CORE_DIR: Optional[Path] = None
    _RAG_DIR: Optional[Path] = None
    _UI_DIR: Optional[Path] = None
    
    # Configuration cache (lazy-loaded)
    _config_cache: Dict[str, Any] = {}
    
    @classmethod
    def initialize(cls, base_dir: Optional[Path] = None) -> None:
        """
        Initialize configuration with optional base directory.
        
        Args:
            base_dir: Base project directory. If None, uses directory of analyzer.py
        """
        if base_dir is None:
            # Assume analyzer.py is in project root
            base_dir = Path(__file__).parent.parent
        
        cls._BASE_DIR = Path(base_dir).resolve()
        cls._CORE_DIR = cls._BASE_DIR / "core"
        cls._RAG_DIR = cls._BASE_DIR / "rag"
        cls._UI_DIR = cls._BASE_DIR / "ui"
        cls._load_env_file()
    
    @classmethod
    def _load_env_file(cls) -> None:
        """
        Load environment variables from .env file if it exists.
        
        Respects existing environment variables (does not override).
        Uses simple line-by-line parsing to avoid external dependencies.
        """
        env_file = cls._BASE_DIR / ".env"
        if not env_file.exists():
            return
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            # Log warning but don't fail (graceful degradation)
            print(f"Warning: Could not load .env file: {e}")
    
    # ========== LOGGING CONFIGURATION ==========
    
    @classmethod
    def log_level(cls) -> str:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @classmethod
    def log_file(cls) -> Optional[str]:
        """Optional log file path for persistent logging."""
        log_file = os.getenv("LOG_FILE", None)
        if log_file:
            return str(Path(log_file).resolve())
        return None
    
    # ========== FILE PATHS ==========
    
    @classmethod
    def base_dir(cls) -> Path:
        """Get base project directory."""
        if cls._BASE_DIR is None:
            cls.initialize()
        return cls._BASE_DIR
    
    @classmethod
    def core_dir(cls) -> Path:
        """Get core module directory."""
        if cls._CORE_DIR is None:
            cls.initialize()
        return cls._CORE_DIR
    
    @classmethod
    def rag_dir(cls) -> Path:
        """Get RAG module directory."""
        if cls._RAG_DIR is None:
            cls.initialize()
        return cls._RAG_DIR
    
    @classmethod
    def ui_dir(cls) -> Path:
        """Get UI module directory."""
        if cls._UI_DIR is None:
            cls.initialize()
        return cls._UI_DIR
    
    # ========== RAG / EMBEDDING CONFIGURATION ==========
    
    @classmethod
    def embedding_model(cls) -> str:
        """
        Name of the embedding model to use.
        
        Default: 'sentence-transformers/all-MiniLM-L6-v2'
        Smaller, faster model suitable for code analysis.
        """
        return os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    
    @classmethod
    def faiss_index_path(cls) -> Path:
        """Path to FAISS index file."""
        default = cls.rag_dir() / "index.faiss"
        custom = os.getenv("FAISS_INDEX_PATH", None)
        if custom:
            return Path(custom).resolve()
        return default
    
    @classmethod
    def chunks_cache_path(cls) -> Path:
        """Path to code chunks cache file (pickle)."""
        default = cls.rag_dir() / "chunks.pkl"
        custom = os.getenv("CHUNKS_CACHE_PATH", None)
        if custom:
            return Path(custom).resolve()
        return default
    
    # ========== ANALYSIS CONFIGURATION ==========
    
    @classmethod
    def max_file_size_mb(cls) -> int:
        """
        Maximum file size to analyze (in MB).
        
        Files larger than this are skipped to avoid memory issues.
        Default: 10 MB
        """
        try:
            return int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        except ValueError:
            return 10
    
    @classmethod
    def ignore_patterns(cls) -> list[str]:
        """
        Patterns to ignore during analysis (relative paths).
        
        Default: __pycache__, .git, venv, node_modules, etc.
        Comma-separated in environment variable.
        """
        default = "__pycache__,.git,venv,env,.venv,.pytest_cache,.tox,*.egg-info,node_modules"
        patterns_str = os.getenv("IGNORE_PATTERNS", default)
        return [p.strip() for p in patterns_str.split(",")]
    
    # ========== LLM CONFIGURATION ==========
    
    @classmethod
    def llm_provider(cls) -> str:
        """
        LLM provider to use ('groq', 'ollama', 'openai', or 'dummy').
        
        Default: 'dummy' (for development without API keys)
        """
        return os.getenv("LLM_PROVIDER", "dummy").lower()
    
    @classmethod
    def groq_api_key(cls) -> Optional[str]:
        """Groq API key (if using Groq provider)."""
        return os.getenv("GROQ_API_KEY", None)
    
    @classmethod
    def openai_api_key(cls) -> Optional[str]:
        """OpenAI API key (if using OpenAI provider)."""
        return os.getenv("OPENAI_API_KEY", None)
    
    @classmethod
    def openai_model(cls) -> str:
        """OpenAI model to use."""
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # ========== API CONFIGURATION ==========
    
    @classmethod
    def api_host(cls) -> str:
        """FastAPI server host (used in Phase 3)."""
        return os.getenv("API_HOST", "localhost")
    
    @classmethod
    def api_port(cls) -> int:
        """FastAPI server port (used in Phase 3)."""
        try:
            return int(os.getenv("API_PORT", "8000"))
        except ValueError:
            return 8000
    
    @classmethod
    def api_debug(cls) -> bool:
        """Enable debug mode in FastAPI (used in Phase 3)."""
        return os.getenv("API_DEBUG", "false").lower() in ("true", "1", "yes")
    
    # ========== UTILITY METHODS ==========
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Export all configuration as dictionary.
        
        Useful for debugging and logging configuration state.
        Sensitive values (API keys) are masked.
        """
        return {
            "log_level": cls.log_level(),
            "log_file": cls.log_file(),
            "base_dir": str(cls.base_dir()),
            "embedding_model": cls.embedding_model(),
            "faiss_index_path": str(cls.faiss_index_path()),
            "max_file_size_mb": cls.max_file_size_mb(),
            "ignore_patterns": cls.ignore_patterns(),
            "llm_provider": cls.llm_provider(),
            "openai_model": cls.openai_model(),
            "api_host": cls.api_host(),
            "api_port": cls.api_port(),
            "api_debug": cls.api_debug(),
            # Sensitive values masked
            "groq_api_key": "***MASKED***" if cls.groq_api_key() else None,
            "openai_api_key": "***MASKED***" if cls.openai_api_key() else None,
        }
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration for issues.
        
        Returns:
            (is_valid, list_of_warnings)
        
        Example:
            is_valid, warnings = Config.validate()
            if not is_valid:
                for warning in warnings:
                    logger.warning(warning)
        """
        warnings = []
        
        # Check required directories exist
        if not cls.base_dir().exists():
            warnings.append(f"Base directory not found: {cls.base_dir()}")
        
        # Warn if FAISS index doesn't exist (RAG not initialized)
        if not cls.faiss_index_path().exists():
            warnings.append(
                f"FAISS index not found: {cls.faiss_index_path()}\n"
                "  Run: python analyzer.py <file> --command index"
            )
        
        # Warn if Groq API key missing for Groq provider
        if cls.llm_provider() == "groq" and not cls.groq_api_key():
            warnings.append(
                "LLM provider set to 'groq' but GROQ_API_KEY not set\n"
                "  Get key from: https://console.groq.com\n"
                "  Set: export GROQ_API_KEY=your_key_here"
            )
        
        # Warn if OpenAI API key missing for OpenAI provider
        if cls.llm_provider() == "openai" and not cls.openai_api_key():
            warnings.append(
                "LLM provider set to 'openai' but OPENAI_API_KEY not set"
            )
        
        return len(warnings) == 0, warnings
