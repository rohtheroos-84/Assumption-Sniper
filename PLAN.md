# plan

all steps are checkboxes and should be marked as they are completed.

## phase 0: alignment and scope
- [x] re-read the prd and confirm the goal, tagline, and target users
- [x] write product principles that enforce "not a chatbot"
- [x] define v1 outcomes and explicit non-goals
- [x] set measurable success metrics and target thresholds
- [x] define quality bars for critique relevance and hallucination rate
- [x] define latency and cost budgets per run
- [x] define data retention and deletion policy
- [x] define privacy and legal constraints
- [x] define a risk register and mitigation owners
- [x] define acceptance criteria for prod readiness

## phase 1: repo and dev environment
- [x] initialize repo and folder layout for frontend, backend, and shared assets
- [x] set node and python version targets
- [x] choose package managers and lockfiles
- [x] configure formatting and linting for js/ts and python
- [x] configure type checking for frontend
- [x] add pre-commit hooks
- [x] define standard scripts for dev, test, lint, format, and build
- [x] create env variable schema and sample values
- [x] write local dev setup instructions
- [x] add basic ci pipeline for lint, test, and build
- [x] add contribution guidelines and code ownership rules

## phase 2: architecture and data design
- [x] finalize request and response shapes for each pipeline stage
- [x] define entities for projects, assumptions, critiques, and simulations
- [x] define scoring model inputs and formulas
- [x] define job lifecycle states and transitions
- [x] design streaming protocol for incremental results
- [x] design caching strategy and cache keys
- [x] design rate limits and quota rules
- [x] choose background job system and queue names
- [x] design audit logging data
- [x] design feature flags for model routing
- [x] create threat model and trust boundaries

## phase 3: backend foundation
- [x] scaffold fastapi app and routing structure
- [x] add config management with environment validation
- [x] add structured logging and request ids
- [x] add health and readiness endpoints
- [x] add database connection pooling
- [x] set up migrations and baseline schema
- [x] implement data access layer for core tables
- [x] implement request validation and size limits
- [x] implement rate limiting middleware

## phase 4: ai layer foundation
- [x] implement openrouter client with timeouts and retries
- [x] define prompt templates for each model role
- [x] define input and output schemas for model responses
- [x] implement response validation and repair
- [x] add safety filters for unsafe content
- [x] add deterministic settings per task type
- [x] add model selection and fallback routing
- [x] add token usage tracking and cost accounting
- [x] add caching for identical requests
- [x] add prompt versioning and experiment ids

## phase 5a: input analysis
- [X] implement idea decomposition service
- [X] store decomposition results
- [X] expose api endpoint for decomposition

## phase 5b: assumption extraction
- [x] implement recursive assumption extraction
- [x] implement assumption chaining with parent links
- [x] implement assumption category classifier
- [x] persist assumptions and relationships
- [x] expose api endpoint for assumption extraction

## phase 5c: skeptic mode
- [x] implement critique generator per assumption
- [x] add critique severity scoring
- [x] persist critiques
- [x] expose api endpoint for critiques

## phase 5d: edge case simulator
- [x] implement scenario generator
- [x] implement impact scoring for scenarios
- [x] persist simulations
- [x] expose api endpoint for simulations

## phase 5e: confidence scoring
- [x] implement confidence score calculator
- [x] implement dependency weight calculation
- [x] implement impact severity calculation
- [x] persist scores
- [x] expose api endpoint for scores

## phase 5f: reconstruction
- [x] implement reconstruction engine
- [x] persist rebuilt idea and rationale
- [x] expose api endpoint for reconstruction

## phase 5g: pipeline orchestration
- [x] implement end-to-end pipeline orchestration
- [x] implement streaming updates for each stage
- [x] implement cancellation and retry
- [x] persist pipeline run metadata

## phase 6: frontend foundation
- [x] scaffold next.js app
- [x] configure tailwindcss and base theme
- [x] create typography scale and spacing system
- [x] implement layout shell and navigation
- [x] implement api client with streaming support
- [x] implement global state for project runs
- [x] implement error and empty states
- [x] add loading and progress indicators
- [x] add basic analytics hooks

## phase 7: core ui screens
- [x] build idea input screen with validation
- [x] build run progress screen with live updates
- [x] build results overview screen
- [x] build assumption list and detail view
- [x] build critique list and severity filters
- [x] build edge case list and impact view
- [x] build reconstruction comparison view
- [x] add shareable report export
- [x] add history list for past runs

## phase 8: visualization dashboard
- [x] implement assumption graph visualization
- [x] implement dependency tree visualization
- [x] implement risk heatmap visualization
- [x] implement confidence radar visualization
- [x] implement contradiction map view
- [x] add interaction patterns: zoom, filter, focus
- [x] add snapshot and export for graphs

## phase 9: multi-agent debate
- [ ] define agent personas and prompts
- [ ] run agents in parallel with timeouts
- [ ] merge and deduplicate agent critiques
- [ ] attribute critiques to agent roles
- [ ] add ui to compare agent perspectives
- [ ] allow toggling agents on or off per run

## phase 10: data and account readiness
- [ ] add user accounts and auth flow
- [ ] add per-user projects and access control
- [ ] add api keys for external access
- [ ] add usage tracking and quotas
- [ ] add team workspace model if needed
- [ ] add billing integration if needed

## phase 11: quality, tests, and evaluation
- [ ] write unit tests for scoring logic
- [ ] write unit tests for prompt parsers
- [ ] write integration tests for pipeline stages
- [ ] write api contract tests
- [ ] add ui component tests
- [ ] add e2e tests for full workflow
- [ ] create evaluation dataset of ideas and expected issues
- [ ] create automated evals for critique relevance
- [ ] add regression tests for prompt changes

## phase 12: performance and reliability
- [ ] add request batching where safe
- [ ] add queue backpressure and retries
- [ ] add cache warming for common prompts
- [ ] add pagination for large result sets
- [ ] add timeouts and circuit breakers for ai calls
- [ ] run load tests and record p95 latencies
- [ ] optimize slow queries and add indexes
- [ ] verify streaming performance under load

## phase 13: security and compliance
- [ ] add input sanitization and prompt injection checks
- [ ] add output filtering for unsafe content
- [ ] add secret management and key rotation
- [ ] add audit logs for sensitive actions
- [ ] add data retention and delete workflows
- [ ] add rate limiting per user and ip
- [ ] run dependency and container scans
- [ ] review permissions for least privilege

## phase 14: observability and ops
- [ ] add structured logs with correlation ids
- [ ] add metrics for latency, cost, and error rates
- [ ] add traces across pipeline stages
- [ ] set up dashboards for kpis and slos
- [ ] add alerting for error spikes and budget burn
- [ ] create runbooks for common incidents
- [ ] set up on-call rotation and escalation

## phase 15: deployment and release
- [ ] containerize frontend and backend
- [ ] set up managed database and redis
- [ ] configure ci and cd with staged deploys
- [ ] set up envs for dev, staging, and prod
- [ ] add migration automation in deploy
- [ ] add blue-green or canary strategy
- [ ] verify rollback plan
- [ ] run staging smoke tests
- [ ] approve production launch checklist

## phase 16: launch and iteration
- [ ] publish landing page and demo flow
- [ ] run private beta with founders and pm users
- [ ] collect feedback and prioritize fixes
- [ ] tune prompts and scoring based on evals
- [ ] improve ux based on session recordings
- [ ] expand model routing for cost and quality balance
- [ ] track success metrics and iterate monthly
- [ ] plan next features from roadmap

## phase 17: prod ready exit criteria
- [ ] p95 latency and error budgets meet targets
- [ ] eval metrics meet quality thresholds
- [ ] security review passed with no critical findings
- [ ] backup and restore tested end to end
- [ ] incident response drills completed
- [ ] docs and runbooks complete
- [ ] release notes prepared
- [ ] owner sign-off for v1 production release
