"""Tests for phase 15 deployment artifacts."""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_smoke_test_in_process_passes():
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_test.py"
    spec = importlib.util.spec_from_file_location("smoke_test", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    import app.db as db_module

    async def fake_check_db():
        return True

    db_module.check_db = fake_check_db

    summary = await module.run_smoke("http://testserver", in_process=True)
    assert summary["passed"] is True
    assert len(summary["checks"]) >= 4


def test_deploy_env_templates_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    assert (root / "deploy/env/development.env").exists()
    assert (root / "deploy/env/staging.env.example").exists()
    assert (root / "deploy/env/production.env.example").exists()


def test_docker_compose_files_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    assert (root / "docker-compose.yml").exists()
    assert (root / "docker-compose.staging.yml").exists()
    assert (root / "docker-compose.production.yml").exists()


def test_launch_checklist_exists():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    assert (root / "docs/deploy/launch-checklist.md").exists()
    assert (root / "docs/deploy/rollback.md").exists()
