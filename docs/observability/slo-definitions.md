# SLO definitions

| SLO | Target | Measurement | Alert |
|-----|--------|-------------|-------|
| API availability | 99.5% monthly | `1 - 5xx/total` from `http_requests_total` | `HighApiErrorRate` |
| API latency p95 | < 500 ms | `http_request_duration_seconds` histogram | `HighApiLatencyP95` |
| Pipeline success | > 95% | failed runs / total runs | `PipelineStageFailures` |
| AI error rate | < 2% | `ai_requests_total{status="error"}` | `AiErrorSpike` |
| Budget burn | < $10/hour | `budget_usd_hourly_total` | `BudgetBurnHigh` |

## Correlation IDs

Every request receives:

- `x-request-id` — per HTTP request
- `x-trace-id` — propagated across services and pipeline stages
- `run_id` — set during pipeline execution and included in structured logs

Structured JSON logs include `request_id`, `trace_id`, `run_id`, and `user_id` when available.

## Dashboards

Import `docs/observability/grafana-dashboard.json` into Grafana and point it at your Prometheus datasource.

## Metrics endpoint

Scrape `GET /api/v1/metrics` for Prometheus exposition format.
