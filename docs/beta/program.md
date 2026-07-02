# Private beta program

## Cohorts

| Cohort | Invite code | Audience | Seats |
|--------|-------------|----------|-------|
| Founders | `founder-beta` | Early-stage founders validating ideas | 50 |
| PMs | `pm-beta` | Product managers stress-testing bets | 50 |

Enable beta mode:

```bash
BETA_ENABLED=true
BETA_INVITE_CODES=founder-beta,pm-beta
```

## Onboarding flow

1. Visitor lands on `/` → tries `/demo`
2. Signs up at `/beta` with invite code
3. Runs full pipeline at `/app`
4. Submits feedback via widget

## Feedback prioritization

Review feedback monthly via:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/ops/feedback
```

Prioritize by:

1. Blockers (cannot complete a run)
2. High-frequency UX friction (analytics `feedback_submit` + session replays)
3. Quality issues (eval relevance below 0.6)

Track session events in `analytics_events` for UX iteration.
