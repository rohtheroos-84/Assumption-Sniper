# Product roadmap v2 (post-v1 launch)

Prioritized after Phase 16 launch and beta iteration.

## Now (0–4 weeks)

- [ ] Team workspaces and shared projects
- [ ] Export run reports (PDF / Notion)
- [ ] Email notifications when runs complete
- [ ] Improved debate comparison UI

## Next (1–3 months)

- [ ] Custom critique personas per industry
- [ ] Integration: Linear / Jira issue export from critiques
- [ ] Per-org routing profiles (cost vs quality)
- [ ] Admin dashboard for beta cohort analytics

## Later (3–6 months)

- [ ] Collaborative editing on reconstructed ideas
- [ ] Fine-tuned domain models for fintech / health / marketplace
- [ ] Public API for CI-driven idea checks
- [ ] Mobile-optimized run review

## Deprioritized

- Open-ended chat mode (conflicts with product principles)
- Social sharing feed
- Anonymous public leaderboards

## Success gates for each quarter

| Metric | Target |
|--------|--------|
| Weekly active runs | 50+ |
| Critique eval relevance | ≥ 0.6 avg |
| Beta NPS (feedback rating) | ≥ 4.0 |
| p95 run latency | < 3 min |

Review monthly with `python apps/api/scripts/monthly_metrics.py` and eval tuning report.
