from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Assumption, AssumptionEdge, Critique, Score, Simulation


def compute_risk_score(*, confidence: int, dep_count: int, max_impact: int) -> int:
    """Higher risk when confidence is low, impact is high, and dependencies are numerous."""
    return int(min(100, (100 - confidence) * (max_impact / 100) * (1 + dep_count / 5)))


def max_simulation_impact_for_assumption(
    *,
    assumption_id: str,
    assumption_text: str,
    simulations: list[Simulation],
) -> int:
    max_impact = 0
    for sim in simulations:
        affected = sim.affected_assumptions_json or []
        try:
            if assumption_id in affected or assumption_text in affected:
                if sim.impact is not None:
                    max_impact = max(max_impact, int(sim.impact))
        except Exception:
            continue
    return max_impact


async def create_score(session: AsyncSession, project_id: str, assumption_id: str, *, confidence_score: int | None, dependency_weight: int | None, impact_severity: int | None, evidence_strength: int | None, risk_score: int | None) -> Score:
    s = Score(
        project_id=project_id,
        assumption_id=assumption_id,
        confidence_score=confidence_score,
        dependency_weight=dependency_weight,
        impact_severity=impact_severity,
        evidence_strength=evidence_strength,
        risk_score=risk_score,
    )
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return s


async def compute_and_persist_scores(session: AsyncSession, project_id: str) -> list[Score]:
    # gather assumptions
    q = select(Assumption).where(Assumption.project_id == project_id)
    r = await session.execute(q)
    assumptions = r.scalars().all()

    results: list[Score] = []

    for a in assumptions:
        # confidence fallback
        confidence = int(a.confidence_score) if a.confidence_score is not None else 50

        # dependency weight = number of edges where this assumption is parent or child
        qd = select(func.count(AssumptionEdge.id)).where(
            (AssumptionEdge.parent_id == a.id) | (AssumptionEdge.child_id == a.id)
        )
        rd = await session.execute(qd)
        dep_count = int(rd.scalar() or 0)

        # evidence strength = number of critiques
        qc = select(func.count(Critique.id)).where(Critique.assumption_id == a.id)
        rc = await session.execute(qc)
        critique_count = int(rc.scalar() or 0)

        # impact severity = max simulation impact affecting this assumption
        qs = select(Simulation).where(Simulation.project_id == project_id)
        rs = await session.execute(qs)
        sims = rs.scalars().all()
        max_impact = max_simulation_impact_for_assumption(
            assumption_id=a.id,
            assumption_text=a.assumption_text,
            simulations=sims,
        )

        risk = compute_risk_score(confidence=confidence, dep_count=dep_count, max_impact=max_impact)

        score = await create_score(
            session,
            project_id,
            a.id,
            confidence_score=confidence,
            dependency_weight=dep_count,
            impact_severity=max_impact,
            evidence_strength=critique_count,
            risk_score=risk,
        )
        results.append(score)

    return results


async def list_scores_for_project(
    session: AsyncSession,
    project_id: str,
    *,
    limit: int,
    cursor: str | None = None,
):
    from app.core.pagination import paginate_by_id

    stmt = select(Score).where(Score.project_id == project_id)
    return await paginate_by_id(session, stmt, id_column=Score.id, limit=limit, cursor=cursor)
