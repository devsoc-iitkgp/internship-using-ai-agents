"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = Field(
        default="", 
        alias="OPENAI_API_KEY",
        description="OpenAI API key for LLM operations"
    )
    serper_api_key: str = Field(
        default="", 
        alias="SERPER_API_KEY",
        description="Serper API key for Google search (free tier: 2500/month)"
    )
    tavily_api_key: Optional[str] = Field(
        default=None, 
        alias="TAVILY_API_KEY",
        description="Optional Tavily API key (legacy)"
    )
    
    # Scraping settings
    scraper_delay: float = Field(
        default=2.0, 
        alias="SCRAPER_DELAY",
        description="Delay between requests in seconds"
    )
    scraper_timeout: int = Field(
        default=30,
        alias="SCRAPER_TIMEOUT", 
        description="Request timeout in seconds"
    )
    
    # Directory paths
    data_dir: Path = Field(
        default=Path("./data"),
        alias="DATA_DIR",
        description="Base data directory"
    )
    output_dir: Path = Field(
        default=Path("./data/outputs"),
        alias="OUTPUT_DIR",
        description="Output directory for generated content"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level"
    )
    
    # LLM settings
    llm_model: str = Field(
        default="gpt-4o",
        alias="LLM_MODEL",
        description="OpenAI model to use"
    )
    llm_temperature: float = Field(
        default=0.3,
        alias="LLM_TEMPERATURE",
        description="LLM temperature for generation"
    )
    
    # IIT KGP specific
    faculty_base_url: str = Field(
        default="https://www.iitkgp.ac.in",
        description="Base URL for IIT KGP website"
    )
    faculty_list_url: str = Field(
        default="https://www.iitkgp.ac.in/faclistbydepartment",
        description="URL for faculty directory"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(exist_ok=True)
        (self.data_dir / "enriched").mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
