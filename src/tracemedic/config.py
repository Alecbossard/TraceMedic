from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRACEMEDIC_", extra="ignore")
    root: Path = ROOT
    data_dir: Path = ROOT / "data"
    provider: str = "ollama"
    model: str = "tracemedic-qwen3:4b"
    model_url: str = "http://127.0.0.1:11434"
    api_key: str = ""
    model_timeout: float = Field(default=90, ge=0.1, le=600)
    tool_timeout: float = Field(default=15, ge=0.1, le=60)
    max_calls: int = Field(default=18, ge=1, le=100)
    max_tools: int = Field(default=14, ge=1, le=100)
    max_steps: int = Field(default=40, ge=1, le=200)
    max_agent_turns: int = Field(default=10, ge=1, le=50)
    max_output_tokens: int = Field(default=1200, ge=64, le=4096)
    context_tokens: int = Field(default=8192, ge=2048, le=32768)
    seed: int = 17
    temperature: float = 0

    @property
    def audit_db(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "audit.db"

    @property
    def checkpoint_db(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "checkpoints.db"
