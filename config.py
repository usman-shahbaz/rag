"""
Configuration classes for different environments.
Values are read from environment variables (populated via .env).
"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class BaseConfig:
    # Flask
    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me"))
    LOG_LEVEL: str = "INFO"

    # CORS – comma-separated origins in env var
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
    )

    # AWS
    AWS_REGION: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    AWS_ACCESS_KEY_ID: str = field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID", ""))
    AWS_SECRET_ACCESS_KEY: str = field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY", ""))
    S3_BUCKET_NAME: str = field(default_factory=lambda: os.getenv("S3_BUCKET_NAME", "rag-support-docs"))

    # Bedrock
    BEDROCK_EMBED_MODEL: str = field(
        default_factory=lambda: os.getenv(
            "BEDROCK_EMBED_MODEL",
            "amazon.titan-embed-text-v2:0",  # supports multilingual text
        )
    )
    BEDROCK_LLM_MODEL: str = field(
        default_factory=lambda: os.getenv(
            "BEDROCK_LLM_MODEL",
            "anthropic.claude-3-haiku-20240307-v1:0",
        )
    )
    BEDROCK_MAX_TOKENS: int = 1024

    # FAISS
    FAISS_INDEX_PATH: str = field(default_factory=lambda: os.getenv("FAISS_INDEX_PATH", "/tmp/faiss_index"))
    FAISS_METADATA_PATH: str = field(default_factory=lambda: os.getenv("FAISS_METADATA_PATH", "/tmp/faiss_metadata.pkl"))

    # RAG
    CHUNK_SIZE: int = 800          # characters per chunk
    CHUNK_OVERLAP: int = 150       # overlap between adjacent chunks
    TOP_K_RESULTS: int = 5         # how many chunks to retrieve
    CONFIDENCE_THRESHOLD: float = 0.30  # below this → fallback answer

    # File upload
    MAX_CONTENT_LENGTH: int = 20 * 1024 * 1024  # 20 MB


@dataclass
class DevelopmentConfig(BaseConfig):
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class ProductionConfig(BaseConfig):
    LOG_LEVEL: str = "INFO"


@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool = True
    LOG_LEVEL: str = "DEBUG"
    S3_BUCKET_NAME: str = "test-bucket"
    FAISS_INDEX_PATH: str = "/tmp/test_faiss_index"
    FAISS_METADATA_PATH: str = "/tmp/test_faiss_metadata.pkl"


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(env: str = "production"):
    """Return an instantiated config object for the given environment name."""
    cls = _CONFIG_MAP.get(env, ProductionConfig)
    return cls()
