from __future__ import annotations

from enum import Enum

from app.ai.schemas import ModelRole
from app.core.config import get_settings

settings = get_settings()


class RoutingProfile(str, Enum):
    cost = "cost"
    balanced = "balanced"
    quality = "quality"


def resolve_model_for_role(role: ModelRole, profile: RoutingProfile | str) -> tuple[str, str]:
    """Return (primary_model, fallback_model) for a role under the given profile."""
    profile_value = RoutingProfile(profile) if not isinstance(profile, RoutingProfile) else profile
    fast = settings.openrouter_fast_model
    reasoning = settings.openrouter_reasoning_model
    fallback = settings.openrouter_fallback_model

    cost_map = {
        ModelRole.decomposition: (fast, fallback),
        ModelRole.extraction: (fast, fallback),
        ModelRole.classifier: (fast, fallback),
        ModelRole.skeptic: (fast, fallback),
        ModelRole.simulator: (fast, fallback),
        ModelRole.reconstruction: (fast, fallback),
    }
    balanced_map = {
        ModelRole.decomposition: (fast, fallback),
        ModelRole.extraction: (fast, fallback),
        ModelRole.classifier: (fast, fallback),
        ModelRole.skeptic: (reasoning, fallback),
        ModelRole.simulator: (reasoning, fallback),
        ModelRole.reconstruction: (reasoning, fallback),
    }
    quality_map = {
        ModelRole.decomposition: (reasoning, fallback),
        ModelRole.extraction: (reasoning, fallback),
        ModelRole.classifier: (fast, fallback),
        ModelRole.skeptic: (reasoning, fallback),
        ModelRole.simulator: (reasoning, fallback),
        ModelRole.reconstruction: (reasoning, fallback),
    }

    table = {
        RoutingProfile.cost: cost_map,
        RoutingProfile.balanced: balanced_map,
        RoutingProfile.quality: quality_map,
    }[profile_value]
    return table[role]
