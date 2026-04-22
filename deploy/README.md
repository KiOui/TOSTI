# Deployment

Production deployment for TOSTI runs on a Docker Compose stack on a VM, orchestrated by `.github/workflows/deploy.yaml`. Every successful push to `master` (after testing, linting, and image build all pass) is deployed automatically.

## Contents of this directory

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Service definitions: `caddy`, `yivi`, `database`, `web`, `cron`. All tuneable values come from `.env`. |
| `Caddyfile` | Caddy reverse proxy config for `tosti.science.ru.nl` and `yivi.tosti.science.ru.nl`. |
| `.env.example` | Template for the `.env` file the workflow writes on the VM. Never commit a real `.env`. |

## VM prerequisites (one-time setup)

- Deploy user (e.g. `deploy-tosti`) exists with a home directory at the deploy path (e.g. `/opt/tosti`).
- Deploy user is in the `docker` group so it can run `docker compose` without sudo.
- Docker Engine + Compose plugin installed.
- The deploy user's `~/.ssh/authorized_keys` contains the public half of the `DEPLOY_SSH_KEY` secret.
- SAML private key + public cert already on the VM under `/opt/tosti/saml/` (overwritten by each deploy from the GitHub secrets).

## GitHub Environment

The workflow runs against a GitHub Environment named **`tosti.science.ru.nl`**. Scope secrets to this Environment (Settings → Environments) so a compromised PR on another branch cannot exfiltrate them. Add required reviewers for extra safety.

### Environment secrets

| Secret | Purpose |
| --- | --- |
| `DEPLOY_SSH_KEY` | Private SSH key for the deploy user. |
| `POSTGRES_PASSWORD` | Postgres password. |
| `DJANGO_SECRET_KEY` | Django secret key. |
| `YIVI_TOKEN` | Yivi server token. |
| `SENTRY_DSN` | Sentry DSN for error reporting. |
| `SAML_PRIVATE_KEY` | Full PEM of the SAML SP private key. |
| `SAML_PUBLIC_CERT` | Full PEM of the SAML SP public certificate. |

### Environment variables (not secret)

| Variable | Example | Purpose |
| --- | --- | --- |
| `DEPLOY_USER` | `deploy-tosti` | SSH username on the VM. |
| `DEPLOY_HOST` | `tosti.vm.science.ru.nl` | SSH hostname of the VM. |
| `DEPLOY_DIR` | `/opt/tosti` | Deploy target directory on the VM. |
| `DEPLOY_SSH_KNOWN_HOSTS` | output of `ssh-keyscan <host>` | Pins the VM's host key. **Without this, SSH will fail in CI.** |
| `DJANGO_HOSTNAME` | `tosti.science.ru.nl` | Public hostname served by Caddy for the Django app. |
| `YIVI_HOSTNAME` | `yivi.tosti.science.ru.nl` | Public hostname served by Caddy for the Yivi server. |
| `DJANGO_ALLOWED_HOSTS` | `tosti.science.ru.nl` | Django's `ALLOWED_HOSTS`. |
| `SAML_ENTITY_ID` | `tosti.science.ru.nl` | SAML entity ID. |
| `EMAIL_HOST` | `smtp.science.ru.nl` | SMTP server. |
| `EMAIL_PORT` | `25` | SMTP port. |
| `EMAIL_ADDRESS` | `www-tosti@science.ru.nl` | From/sender address; used for `EMAIL_HOST_USER`, `EMAIL_DEFAULT_SENDER`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`. |

## What the workflow does

1. Rsyncs `deploy/docker-compose.yml` and `deploy/Caddyfile` to `$DEPLOY_DIR/` on the VM.
2. Materializes the SAML key/cert from secrets and rsyncs them to `$DEPLOY_DIR/saml/`.
3. Writes `$DEPLOY_DIR/.env` (mode 600) from the Environment's secrets and vars.
4. Runs `docker compose pull && docker compose up -d --remove-orphans`.
5. Polls `docker inspect` until `tosti-web-1` reports `healthy`; fails the job if it doesn't within ~5 minutes.

## Rollback

Every master commit is published to `ghcr.io/kioui/tosti:sha-<commit-sha>` (full 40-char SHA) in addition to `:latest`. To roll back:

```bash
ssh deploy-tosti@<vm>
cd /opt/tosti
# Edit docker-compose.yml to pin the previous image, e.g.:
#   image: ghcr.io/kioui/tosti:sha-abc123...
docker compose up -d
```

## Local verification before first deploy

Temporarily change the workflow's `on:` trigger to `workflow_dispatch` to run it manually from the Actions tab. Add a preliminary SSH check step (`ssh ... 'echo hello && docker ps'`) to confirm credentials and host access before letting the real deploy run.
