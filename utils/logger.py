"""
Structured logging module for the code modernization platform.

Design Rationale:
- Provides both console and file logging capabilities
- Supports context injection (e.g., current file being analyzed)
- Uses standard library logging for compatibility and zero dependencies
- Designed to integrate easily with logging aggregation services later
- Structured format enables log parsing and monitoring

Architecture Pattern:
- Single logger instance (factory pattern) avoids duplication
- Context manager for temporary context (e.g., analyzing a specific file)
- Log levels controlled via environment variable or configuration
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log lines with context.
    
    Supports injection of contextual information (file name, analysis stage, etc.)
    into every log message for better traceability.
    """
    
    def __init__(self, include_timestamp: bool = True):
        """Initialize formatter with optional timestamp."""
        self.include_timestamp = include_timestamp
        super().__init__()
        self._context: Dict[str, Any] = {}
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set contextual information to be included in logs."""
        self._context = context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with context information."""
        # Build context string
        context_parts = []
        if self._context:
            for key, value in self._context.items():
                context_parts.append(f"{key}={value}")
        context_str = " [" + " ".join(context_parts) + "]" if context_parts else ""
        
        # Build timestamp string
        timestamp_str = ""
        if self.include_timestamp:
            timestamp_str = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        
        # Build level string with padding
        level_str = f"[{record.levelname:8}]"
        
        # Combine all parts
        message = record.getMessage()
        return f"{timestamp_str}{level_str} {message}{context_str}"


class Logger:
    """
    Wrapper around Python's logging module with structured logging support.
    
    Provides:
    - Consistent log formatting across the application
    - Context injection for traceability
    - Easy enable/disable of file logging
    - Log level management
    """
    
    _instance: Optional['Logger'] = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize the logging system.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for file logging
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_file = log_file
        self._formatter = StructuredFormatter(include_timestamp=True)
        self._context: Dict[str, Any] = {}
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger for the given module name.
        
        Args:
            name: Module name (typically __name__)
        
        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        logger.propagate = False
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self._formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self._formatter)
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set global context that will be added to all log messages.
        
        Useful for tracking which file/module is currently being analyzed.
        
        Args:
            context: Dictionary of context information
        
        Example:
            logger_instance.set_context({"file": "config.py", "stage": "parsing"})
        """
        self._context = context
        self._formatter.set_context(context)
    
    def clear_context(self) -> None:
        """Clear all context information."""
        self._context = {}
        self._formatter.set_context({})
    
    @contextmanager
    def temporary_context(self, **kwargs) -> None:
        """
        Temporarily add context information for a block of code.
        
        Context is restored to its previous state when the block exits.
        
        Example:
            with logger_instance.temporary_context(file="app.py", stage="extraction"):
                # All logs here will include file=app.py and stage=extraction
                logger.info("Processing module")
        """
        old_context = self._context.copy()
        try:
            self._context.update(kwargs)
            self._formatter.set_context(self._context)
            yield
        finally:
            self._context = old_context
            self._formatter.set_context(old_context)
    
    @classmethod
    def initialize(cls, log_level: str = "INFO", log_file: Optional[str] = None) -> 'Logger':
        """
        Initialize the singleton logger instance.
        
        Should be called once at application startup.
        
        Args:
            log_level: Logging level
            log_file: Optional file path for persistent logging
        
        Returns:
            Logger instance
        """
        if cls._instance is None:
            cls._instance = cls(log_level=log_level, log_file=log_file)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """Get the singleton logger instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Convenience function for getting loggers in modules
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given module name.
    
    Convenience function to be used throughout the codebase.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    return Logger.get_instance().get_logger(name)
