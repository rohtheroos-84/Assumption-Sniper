from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_user_id", "user_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    input_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (Index("ix_runs_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String, default="queued")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    model_profile = Column(String, nullable=True)
    cost_usd = Column(Numeric(10, 4), nullable=True)
    token_total = Column(Integer, nullable=True)

    project = relationship("Project")


class Assumption(Base):
    __tablename__ = "assumptions"
    __table_args__ = (Index("ix_assumptions_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assumption_text = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    impact_score = Column(Integer, nullable=True)

    project = relationship("Project")


class AssumptionEdge(Base):
    __tablename__ = "assumption_edges"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    parent_id = Column(String, ForeignKey("assumptions.id"), nullable=True)
    child_id = Column(String, ForeignKey("assumptions.id"), nullable=False)
    depth = Column(Integer, nullable=False, default=1)


class Critique(Base):
    __tablename__ = "critiques"
    __table_args__ = (Index("ix_critiques_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assumption_id = Column(String, ForeignKey("assumptions.id"), nullable=False)
    critique_text = Column(Text, nullable=False)
    severity = Column(Integer, nullable=True)


class Simulation(Base):
    __tablename__ = "simulations"
    __table_args__ = (Index("ix_simulations_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    scenario = Column(Text, nullable=False)
    impact = Column(Integer, nullable=True)
    likelihood = Column(Integer, nullable=True)
    affected_assumptions_json = Column(JSON, nullable=True)


class Reconstruction(Base):
    __tablename__ = "reconstructions"
    __table_args__ = (Index("ix_reconstructions_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    rebuilt_idea = Column(Text, nullable=False)
    key_changes_json = Column(JSON, nullable=True)
    risk_reductions_json = Column(JSON, nullable=True)


class Decomposition(Base):
    __tablename__ = "decompositions"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    run_id = Column(String, ForeignKey("runs.id"), nullable=True)
    output_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (Index("ix_scores_project_id", "project_id"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assumption_id = Column(String, ForeignKey("assumptions.id"), nullable=False)
    confidence_score = Column(Integer, nullable=True)
    dependency_weight = Column(Integer, nullable=True)
    impact_severity = Column(Integer, nullable=True)
    evidence_strength = Column(Integer, nullable=True)
    risk_score = Column(Integer, nullable=True)


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (Index("ix_run_events_run_id_created_at", "run_id", "created_at"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    stage = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    actor_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    status = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_json = Column(JSON, nullable=True)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (Index("ix_usage_records_user_id_created_at", "user_id", "created_at"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=True)
    tokens = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
