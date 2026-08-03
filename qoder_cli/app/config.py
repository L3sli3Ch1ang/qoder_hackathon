"""SkillBridge configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables with sensible defaults."""

    MODEL_EMBEDDING: str = "sentence-transformers/all-MiniLM-L6-v2"
    MODEL_RERANKER: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    QDRANT_PATH: str = "./qdrant_data"
    SEED_DATA_PATH: str = "./app/data"

    # DashScope (Alibaba Cloud Model Studio) for narrative generation
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_MODEL: str = "qwen-plus"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Pipeline parameters
    BM25_TOP_K: int = 50
    DENSE_TOP_K: int = 50
    RRF_TOP_K: int = 30
    RERANK_TOP_K: int = 10
    RRF_K: int = 60

    model_config = {"env_prefix": "SKILLBRIDGE_"}


settings = Settings()
