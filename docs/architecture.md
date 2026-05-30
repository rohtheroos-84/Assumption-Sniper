# architecture

this document completes architecture and data design.

## 1. request and response shapes

### 1.1 base run request

```
post /api/v1/runs
{
  "title": "string",
  "input_text": "string",
  "options": {
    "agents": ["investor", "engineer", "marketer", "competitor", "customer", "operations"],
    "enable_streaming": true,
    "max_depth": 3,
    "language": "en",
    "strict_mode": false
  }
}
```

### 1.2 base run response

```
{
  "run_id": "uuid",
  "project_id": "uuid",
  "status": "queued",
  "created_at": "iso-8601",
  "links": {
    "events": "/api/v1/runs/{run_id}/events",
    "result": "/api/v1/runs/{run_id}"
  }
}
```

### 1.3 stage inputs and outputs

#### input analysis (decomposition)

input: `{ "input_text": "string" }`

output:

```
{
  "targets": ["string"],
  "goals": ["string"],
  "dependencies": ["string"],
  "operational_requirements": ["string"]
}
```

#### assumption extraction

input: `{ "input_text": "string", "max_depth": 3 }`

output:

```
{
  "assumptions": [
    {
      "assumption_id": "uuid",
      "assumption_text": "string",
      "category": "financial|behavioral|technical|operational|legal|scalability|adoption",
      "parent_id": "uuid|null",
      "depth": 1
    }
  ]
}
```

#### skeptic mode (critiques)

input: `{ "assumptions": ["assumption_id"] }`

output:

```
{
  "critiques": [
    {
      "critique_id": "uuid",
      "assumption_id": "uuid",
      "critique_text": "string",
      "severity": 0,
      "rationale": "string"
    }
  ]
}
```

#### edge case simulator

input: `{ "input_text": "string", "assumptions": ["assumption_id"] }`

output:

```
{
  "simulations": [
    {
      "simulation_id": "uuid",
      "scenario": "string",
      "likelihood": 0,
      "impact": 0,
      "affected_assumptions": ["assumption_id"]
    }
  ]
}
```

#### confidence scoring

input: `{ "assumptions": ["assumption_id"], "critiques": ["critique_id"], "simulations": ["simulation_id"] }`

output:

```
{
  "scores": [
    {
      "assumption_id": "uuid",
      "confidence_score": 0,
      "dependency_weight": 0,
      "impact_severity": 0,
      "evidence_strength": 0,
      "risk_score": 0
    }
  ]
}
```

#### reconstruction

input: `{ "input_text": "string", "scores": ["assumption_id"], "critiques": ["critique_id"] }`

output:

```
{
  "rebuilt_idea": "string",
  "key_changes": ["string"],
  "risk_reductions": ["string"],
  "new_assumptions": ["string"]
}
```

### 1.4 run result shape

```
{
  "run_id": "uuid",
  "status": "completed|failed|cancelled",
  "summary": {
    "top_risks": ["string"],
    "weak_assumptions": ["assumption_id"],
    "rebuild_excerpt": "string"
  },
  "results": {
    "decomposition": {"...": "..."},
    "assumptions": ["..."],
    "critiques": ["..."],
    "simulations": ["..."],
    "scores": ["..."],
    "reconstruction": {"...": "..."}
  }
}
```

## 2. entities and data model

### core tables

- users: id, email, created_at
- projects: id, user_id, title, input_text, created_at
- runs: id, project_id, status, started_at, finished_at, model_profile, cost_usd, token_total
- assumptions: id, project_id, assumption_text, category, confidence_score, impact_score
- assumption_edges: id, project_id, parent_id, child_id, depth
- critiques: id, project_id, assumption_id, critique_text, severity
- simulations: id, project_id, scenario, impact, likelihood
- reconstructions: id, project_id, rebuilt_idea, key_changes_json, risk_reductions_json
- scores: id, project_id, assumption_id, confidence_score, dependency_weight, impact_severity, evidence_strength, risk_score
- run_events: id, run_id, stage, event_type, payload_json, created_at
- audit_log: id, actor_id, action, resource_type, resource_id, status, request_id, ip, user_agent, created_at, meta_json

### indexes (minimum)

- projects(user_id, created_at)
- runs(project_id, created_at)
- assumptions(project_id)
- critiques(project_id, assumption_id)
- simulations(project_id)
- run_events(run_id, created_at)

## 3. scoring model inputs and formulas

### inputs (0-100)

- evidence_strength: model-estimated strength of evidence for the assumption
- critique_severity: severity from skeptic mode (0-100, higher is worse)
- dependency_weight: graph centrality or chokepoint score
- impact_severity: worst-case impact from simulations

### formulas

```
confidence_score = clamp(0, 100, round(0.6 * evidence_strength + 0.4 * (100 - critique_severity)))

risk_score = round((100 - confidence_score) * (dependency_weight / 100) * (impact_severity / 100))
```

## 4. job lifecycle states

states: queued -> running -> streaming -> completed
alternate: queued -> running -> failed
alternate: queued -> cancelled
alternate: running -> retrying -> running

## 5. streaming protocol

use server-sent events (SSE) at `/api/v1/runs/{run_id}/events`.

event types:
- stage_start
- stage_progress
- stage_complete
- stage_error
- run_complete

payload example:

```
event: stage_progress
data: {"run_id":"uuid","stage":"assumptions","percent":40,"payload":{...}}
```

## 6. caching strategy and cache keys

use redis for response caching and idempotency.

- cache:decompose:{hash(input_text, prompt_version, model)} ttl 7d
- cache:assumptions:{hash(input_text, max_depth, prompt_version, model)} ttl 7d
- cache:critique:{hash(assumption_id, prompt_version, model)} ttl 7d
- cache:simulate:{hash(input_text, prompt_version, model)} ttl 7d
- cache:rebuild:{hash(input_text, scores_hash, prompt_version, model)} ttl 7d
- idempotency:{idempotency_key} ttl 24h

## 7. rate limits and quotas

defaults (can be tiered later):
- run creation: 10 per hour per user, 2 concurrent runs per user
- read endpoints: 60 requests per minute per user
- ip guardrail: 120 requests per minute per ip
- burst limit: 5 run creations in 60 seconds per user

## 8. background job system and queues

use arq + redis for async jobs.

queues:
- pipeline: orchestration and stage sequencing
- ai: openrouter calls and prompt execution
- scoring: score calculation and aggregation
- maintenance: cleanup and cache invalidation

## 9. audit logging data

store a record for: run creation, run cancel, model route change, admin overrides, data deletion.

fields:
- id, actor_id, action, resource_type, resource_id, status
- request_id, ip, user_agent, created_at, meta_json

## 10. feature flags for model routing

flags:
- ff_multi_agent_enabled
- ff_edge_simulator_enabled
- ff_reconstruction_enabled
- ff_streaming_enabled
- ff_model_fallback_enabled
- ff_cost_guard_enabled
- ff_routing_profile (string)

## 11. threat model and trust boundaries

### trust boundaries
- user client -> api gateway
- api -> worker queue
- api/worker -> postgres and redis
- api/worker -> openrouter (external)

### primary threats
- prompt injection and instruction smuggling
- abuse and spam runs to exhaust budget
- data leakage to third-party model providers
- broken access control between users and projects
- replay of old runs or idempotency keys
- streaming endpoint data exposure

### required mitigations
- input sanitization and prompt hardening
- strict authz on project and run access
- per-user and per-ip rate limits
- redaction of sensitive tokens in logs
- scoped api keys for external access
- encryption at rest and in transit
