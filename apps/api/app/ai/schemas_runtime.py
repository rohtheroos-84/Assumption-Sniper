from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class DecompositionOutput(BaseModel):
    targets: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    operational_requirements: list[str] = Field(default_factory=list)


class AssumptionItem(BaseModel):
    assumption_id: Optional[str] = None
    assumption_text: str
    category: str
    parent_id: Optional[str] = None
    depth: int = Field(default=1, ge=1)


class AssumptionsOutput(BaseModel):
    assumptions: list[AssumptionItem] = Field(default_factory=list)


class ClassificationItem(BaseModel):
    assumption_text: str
    category: str


class ClassificationOutput(BaseModel):
    classifications: list[ClassificationItem] = Field(default_factory=list)


class CritiqueItem(BaseModel):
    critique_id: Optional[str] = None
    assumption_id: Optional[str] = None
    critique_text: str
    severity: int = Field(ge=0, le=100)
    rationale: Optional[str] = None


class CritiquesOutput(BaseModel):
    critiques: list[CritiqueItem] = Field(default_factory=list)


class SimulationItem(BaseModel):
    simulation_id: Optional[str] = None
    scenario: str
    likelihood: int = Field(ge=0, le=100)
    impact: int = Field(ge=0, le=100)
    affected_assumptions: list[str] = Field(default_factory=list)


class SimulationsOutput(BaseModel):
    simulations: list[SimulationItem] = Field(default_factory=list)


class ReconstructionOutput(BaseModel):
    rebuilt_idea: str
    key_changes: list[str] = Field(default_factory=list)
    risk_reductions: list[str] = Field(default_factory=list)
    new_assumptions: list[str] = Field(default_factory=list)


class ValidationRepairResult(BaseModel):
    parsed: dict[str, Any]
    repaired: bool = False
    warnings: list[str] = Field(default_factory=list)
