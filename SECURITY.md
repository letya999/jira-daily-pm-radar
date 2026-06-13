# Security Policy

This project is read-only by design. It fetches Jira data and produces local reports.

## Secrets

Never commit:

- `.env`
- Jira tokens
- API keys
- cookies/session dumps
- raw company Jira exports
- report artifacts produced from real Jira data

## Recommended local setup

```bash
uv sync --all-extras
uv run pre-commit install
uv run pre-commit run --all-files
```

## CI security checks

GitHub Actions runs:

- Bandit
- detect-secrets
- Gitleaks
- pip-audit
- custom secret scanner

## Reporting vulnerabilities

Open a private security advisory or contact the maintainer directly.
