"""Logging configuration for observability."""

import logging
import sys
from typing import Optional
from .config import settings


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Optional override for log level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level from settings or override
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Only add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


class AgentLogger:
    """
    Structured logger for agent operations.
    
    Provides consistent logging format for tracking agent execution.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._logger = get_logger(f"agent.{agent_name}")
        self.logs: list[str] = []
    
    def info(self, message: str, **kwargs) -> None:
        """Log info level message."""
        formatted = self._format_message(message, kwargs)
        self._logger.info(formatted)
        self.logs.append(f"INFO: {formatted}")
    
    def error(self, message: str, **kwargs) -> None:
        """Log error level message."""
        formatted = self._format_message(message, kwargs)
        self._logger.error(formatted)
        self.logs.append(f"ERROR: {formatted}")
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning level message."""
        formatted = self._format_message(message, kwargs)
        self._logger.warning(formatted)
        self.logs.append(f"WARNING: {formatted}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug level message."""
        formatted = self._format_message(message, kwargs)
        self._logger.debug(formatted)
    
    def _format_message(self, message: str, context: dict) -> str:
        """Format message with context."""
        if context:
            ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"[{self.agent_name}] {message} | {ctx_str}"
        return f"[{self.agent_name}] {message}"
    
    def get_logs(self) -> list[str]:
        """Get all logged messages for this agent session."""
        return self.logs.copy()
