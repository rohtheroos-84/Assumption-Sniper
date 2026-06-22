from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.safety import sanitize_text


class AITask(str, Enum):
    decomposition = "decomposition"
    assumptions = "assumptions"
    assumption_classification = "assumption_classification"
    critique = "critique"
    simulation = "simulation"
    reconstruction = "reconstruction"


class ModelRole(str, Enum):
    decomposition = "decomposition"
    extraction = "extraction"
    classifier = "classifier"
    skeptic = "skeptic"
    simulator = "simulator"
    reconstruction = "reconstruction"


class AIRequest(BaseModel):
    task: AITask
    input_text: str = Field(min_length=1)
    project_id: Optional[str] = None
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    dry_run: bool = True
    max_depth: int = Field(default=3, ge=1, le=8)

    @field_validator("input_text")
    @classmethod
    def sanitize_input(cls, value: str) -> str:
        return sanitize_text(value)


class DebateRequest(BaseModel):
    input_text: str = Field(min_length=1)
    project_id: Optional[str] = None
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    dry_run: bool = True
    persona_keys: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=12.0, ge=1.0, le=60.0)
    max_agents: int = Field(default=3, ge=1, le=8)

    @field_validator("input_text")
    @classmethod
    def sanitize_input(cls, value: str) -> str:
        return sanitize_text(value)


class PromptMetadata(BaseModel):
    prompt_version: str
    experiment_id: str
    model: str
    fallback_model: Optional[str] = None
    cached: bool = False
    safety_blocked: bool = False


class AIResult(BaseModel):
    task: AITask
    metadata: PromptMetadata
    raw_output: Optional[str] = None
    parsed_output: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
