# plan

all steps are checkboxes and should be marked as they are completed.

## phase 0: alignment and scope
- [x] re-read the prd and confirm the goal, tagline, and target users
- [x] write product principles that enforce "not a chatbot"
- [ ] define v1 outcomes and explicit non-goals
- [ ] set measurable success metrics and target thresholds
- [ ] define quality bars for critique relevance and hallucination rate
- [ ] define latency and cost budgets per run
- [ ] define data retention and deletion policy
- [ ] define privacy and legal constraints
- [ ] define a risk register and mitigation owners
- [ ] define acceptance criteria for prod readiness

## phase 1: repo and dev environment
- [ ] initialize repo and folder layout for frontend, backend, and shared assets
- [ ] set node and python version targets
- [ ] choose package managers and lockfiles
- [ ] configure formatting and linting for js/ts and python
- [ ] configure type checking for frontend
- [ ] add pre-commit hooks
- [ ] define standard scripts for dev, test, lint, format, and build
- [ ] create env variable schema and sample values
- [ ] write local dev setup instructions
- [ ] add basic ci pipeline for lint, test, and build
- [ ] add contribution guidelines and code ownership rules

## phase 2: architecture and data design
- [ ] finalize request and response shapes for each pipeline stage
- [ ] define entities for projects, assumptions, critiques, and simulations
- [ ] define scoring model inputs and formulas
- [ ] define job lifecycle states and transitions
- [ ] design streaming protocol for incremental results
- [ ] design caching strategy and cache keys
- [ ] design rate limits and quota rules
- [ ] choose background job system and queue names
- [ ] design audit logging data
- [ ] design feature flags for model routing
- [ ] create threat model and trust boundaries

## phase 3: backend foundation
- [ ] scaffold fastapi app and routing structure
- [ ] add config management with environment validation
- [ ] add structured logging and request ids
- [ ] add health and readiness endpoints
- [ ] add database connection pooling
- [ ] set up migrations and baseline schema
- [ ] implement data access layer for core tables
- [ ] implement redis client with connection checks
- [ ] implement error handling middleware with consistent error codes
- [ ] implement request validation and size limits
- [ ] implement rate limiting middleware
- [ ] implement background job runner and worker process
- [ ] implement job status and cancellation endpoints

## phase 4: ai layer foundation
- [ ] implement openrouter client with timeouts and retries
- [ ] define prompt templates for each model role
- [ ] define input and output schemas for model responses
- [ ] implement response validation and repair
- [ ] add safety filters for unsafe content
- [ ] add deterministic settings per task type
- [ ] add model selection and fallback routing
- [ ] add token usage tracking and cost accounting
- [ ] add caching for identical requests
- [ ] add prompt versioning and experiment ids

## phase 5a: input analysis
- [ ] implement idea decomposition service
- [ ] store decomposition results
- [ ] expose api endpoint for decomposition

## phase 5b: assumption extraction
- [ ] implement recursive assumption extraction
- [ ] implement assumption chaining with parent links
- [ ] implement assumption category classifier
- [ ] persist assumptions and relationships
- [ ] expose api endpoint for assumption extraction

## phase 5c: skeptic mode
- [ ] implement critique generator per assumption
- [ ] add critique severity scoring
- [ ] persist critiques
- [ ] expose api endpoint for critiques

## phase 5d: edge case simulator
- [ ] implement scenario generator
- [ ] implement impact scoring for scenarios
- [ ] persist simulations
- [ ] expose api endpoint for simulations

## phase 5e: confidence scoring
- [ ] implement confidence score calculator
- [ ] implement dependency weight calculation
- [ ] implement impact severity calculation
- [ ] persist scores
- [ ] expose api endpoint for scores

## phase 5f: reconstruction
- [ ] implement reconstruction engine
- [ ] persist rebuilt idea and rationale
- [ ] expose api endpoint for reconstruction

## phase 5g: pipeline orchestration
- [ ] implement end-to-end pipeline orchestration
- [ ] implement streaming updates for each stage
- [ ] implement cancellation and retry
- [ ] persist pipeline run metadata

## phase 6: frontend foundation
- [ ] scaffold next.js app
- [ ] configure tailwindcss and base theme
- [ ] create typography scale and spacing system
- [ ] implement layout shell and navigation
- [ ] implement api client with streaming support
- [ ] implement global state for project runs
- [ ] implement error and empty states
- [ ] add loading and progress indicators
- [ ] add basic analytics hooks

## phase 7: core ui screens
- [ ] build idea input screen with validation
- [ ] build run progress screen with live updates
- [ ] build results overview screen
- [ ] build assumption list and detail view
- [ ] build critique list and severity filters
- [ ] build edge case list and impact view
- [ ] build reconstruction comparison view
- [ ] add shareable report export
- [ ] add history list for past runs

## phase 8: visualization dashboard
- [ ] implement assumption graph visualization
- [ ] implement dependency tree visualization
- [ ] implement risk heatmap visualization
- [ ] implement confidence radar visualization
- [ ] implement contradiction map view
- [ ] add interaction patterns: zoom, filter, focus
- [ ] add snapshot and export for graphs

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
