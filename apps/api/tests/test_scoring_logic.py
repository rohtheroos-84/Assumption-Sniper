"""Unit tests for confidence and risk scoring formulas."""

from __future__ import annotations

from types import SimpleNamespace

from app.crud.scores import compute_risk_score, max_simulation_impact_for_assumption


class TestComputeRiskScore:
    def test_zero_impact_yields_zero_risk(self):
        assert compute_risk_score(confidence=30, dep_count=4, max_impact=0) == 0

    def test_high_confidence_lowers_risk(self):
        low_conf = compute_risk_score(confidence=20, dep_count=2, max_impact=80)
        high_conf = compute_risk_score(confidence=80, dep_count=2, max_impact=80)
        assert low_conf > high_conf

    def test_dependencies_increase_risk(self):
        few_deps = compute_risk_score(confidence=50, dep_count=0, max_impact=60)
        many_deps = compute_risk_score(confidence=50, dep_count=10, max_impact=60)
        assert many_deps > few_deps

    def test_caps_at_100(self):
        assert compute_risk_score(confidence=0, dep_count=20, max_impact=100) == 100

    def test_known_formula_value(self):
        # (100 - 40) * (50/100) * (1 + 5/5) = 60 * 0.5 * 2 = 60
        assert compute_risk_score(confidence=40, dep_count=5, max_impact=50) == 60


class TestMaxSimulationImpact:
    def test_matches_by_assumption_id(self):
        sims = [SimpleNamespace(impact=70, affected_assumptions_json=["a-1"])]
        assert (
            max_simulation_impact_for_assumption(
                assumption_id="a-1",
                assumption_text="users want delivery",
                simulations=sims,
            )
            == 70
        )

    def test_matches_by_assumption_text(self):
        sims = [SimpleNamespace(impact=55, affected_assumptions_json=["users want delivery"])]
        assert (
            max_simulation_impact_for_assumption(
                assumption_id="a-1",
                assumption_text="users want delivery",
                simulations=sims,
            )
            == 55
        )

    def test_returns_max_across_simulations(self):
        sims = [
            SimpleNamespace(impact=40, affected_assumptions_json=["a-1"]),
            SimpleNamespace(impact=85, affected_assumptions_json=["a-1"]),
        ]
        assert (
            max_simulation_impact_for_assumption(
                assumption_id="a-1",
                assumption_text="ignored",
                simulations=sims,
            )
            == 85
        )

    def test_no_match_returns_zero(self):
        sims = [SimpleNamespace(impact=90, affected_assumptions_json=["other"])]
        assert (
            max_simulation_impact_for_assumption(
                assumption_id="a-1",
                assumption_text="users want delivery",
                simulations=sims,
            )
            == 0
        )
