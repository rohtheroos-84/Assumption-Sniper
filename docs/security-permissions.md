# Security permissions and least-privilege review

## Authentication surfaces

| Route group | Auth required | Notes |
|-------------|---------------|-------|
| `/api/v1/ping`, `/api/v1/health` | No | Public health checks only |
| `/api/v1/auth/register`, `/api/v1/auth/login` | No | Registration and login |
| `/api/v1/auth/*` (other) | Yes | Active account required |
| `/api/v1/ai/*` | Yes | All AI endpoints require authenticated active user |
| `/api/v1/runs/*` | Yes | Run access scoped to project owner |
| `/api/v1/data/*` | Yes | Delete operations scoped to owner |

## Authorization model

- **Project ownership**: Every run and project is tied to `users.id`. Access checks compare `project.user_id` to the authenticated user.
- **API keys**: Stored as SHA-256 hashes; only the prefix is retained for identification. Keys can be listed, revoked, and rotated by the owning user.
- **Inactive accounts**: Users with pending deletion (`deletion_requested_at` set) or `is_active=false` cannot access protected routes.

## Sensitive actions audited

- User registration and login (success/failure)
- API key create, revoke, rotate
- Run create, start, cancel
- Project delete and account deletion request

Audit records include actor, action, resource, request id, IP, and user agent.

## Data retention

| Data type | Default retention |
|-----------|-------------------|
| Raw inputs/events | 30 days |
| Summaries/scores | 12 months |
| Usage metrics | 24 months |
| Account deletion | 7-day grace period |

Run `apps/api/scripts/purge_retention.py` on a schedule to enforce retention.

## Rate limiting

- Per-IP guardrail on all requests
- Per-user limits derived from JWT subject or API key hash (not spoofable headers)
- Separate limits for run creation, burst, and read endpoints

## Secret handling

- JWT secret and OpenRouter API key loaded from environment only
- API keys never stored in plaintext after creation
- Rotate API keys via `POST /api/v1/auth/apikeys/{id}/rotate`

## CI security checks

- `pip-audit` for dependency vulnerabilities
- `bandit` for common Python security issues
- `trivy` filesystem scan on repository and container image build
