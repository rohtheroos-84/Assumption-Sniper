from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    input_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class Run(Base):
    __tablename__ = "runs"

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

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    assumption_id = Column(String, ForeignKey("assumptions.id"), nullable=False)
    critique_text = Column(Text, nullable=False)
    severity = Column(Integer, nullable=True)


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    scenario = Column(Text, nullable=False)
    impact = Column(Integer, nullable=True)
    likelihood = Column(Integer, nullable=True)


class Reconstruction(Base):
    __tablename__ = "reconstructions"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    rebuilt_idea = Column(Text, nullable=False)
    key_changes_json = Column(JSON, nullable=True)
    risk_reductions_json = Column(JSON, nullable=True)


class Score(Base):
    __tablename__ = "scores"

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
