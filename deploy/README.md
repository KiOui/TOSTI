# Deployment

Production deployment for TOSTI runs on a Docker Compose stack on a VM, orchestrated by `.github/workflows/deploy.yaml`. It fires after the `CI` workflow (test + lint + image build) succeeds on `master`.

The deploy runs on a **self-hosted GitHub Actions runner installed on the VM itself**. The runner polls GitHub over outbound HTTPS; GitHub never connects inbound. This was necessary because the CNCZ network blocks inbound SSH from the public internet, so a push-based model would have needed a VPN or an SSH hole.

## Contents of this directory

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Service definitions: `caddy`, `yivi`, `database`, `web`, `cron`. All tuneable values come from `.env`. |
| `Caddyfile` | Caddy reverse proxy config for `tosti.science.ru.nl` and `yivi.tosti.science.ru.nl`. |
| `.env.example` | Template for the `.env` file the workflow writes on the VM. Never commit a real `.env`. |

## VM prerequisites (one-time setup)

- A `deploy-tosti` system user owns `/opt/tosti/` (mode 770, group-writable).
- A `github-runner` system user exists, in groups `docker` and `deploy-tosti` so it can run `docker compose` and write to `/opt/tosti/`.
- Docker Engine + Compose plugin installed.
- The self-hosted runner is installed under `~github-runner/actions-runner/` and managed by systemd (`actions.runner.KiOui-TOSTI.tosti-vm.service`).
- SAML private key + public cert are under `/opt/tosti/saml/` (overwritten by each deploy from the GitHub secrets). Docker Compose exposes them to the `web` container via Docker secrets, mounted at `/run/secrets/saml_private_key` and `/run/secrets/saml_public_cert`. In non-swarm Compose, the secret file preserves the host file's mode, so the deploy workflow sets the host files to mode 644 (readable by the container's `nobody` user); the parent `/opt/tosti` is mode 770 owned by `deploy-tosti:deploy-tosti`, which gates host-side access.

### Installing the self-hosted runner

Follow [GitHub's self-hosted runner instructions](https://github.com/KiOui/TOSTI/settings/actions/runners/new) — they show the exact `curl` + `./config.sh` commands for the current runner version. Use these settings:

- **User to run as**: `github-runner` (create with `useradd --system --create-home --shell /bin/bash --groups docker,deploy-tosti github-runner`).
- **Runner name**: `tosti-vm`.
- **Labels**: `tosti-vm,production`. `tosti-vm` identifies the machine; `production` is the tier that `deploy.yaml`'s `runs-on:` filters on. When a staging runner is added later, it would be labeled `tosti-staging-vm,staging` and a staging workflow would use `runs-on: [self-hosted, staging]`.
- **Install as a service**: `sudo ./svc.sh install github-runner && sudo ./svc.sh start`.

## GitHub Environment

The workflow runs against a GitHub Environment named **`tosti.science.ru.nl`**. Scope secrets to this Environment (Settings → Environments) so workflows on other branches cannot exfiltrate them. Add required reviewers for extra safety — every deploy waits for human approval.

### Environment secrets

| Secret | Purpose |
| --- | --- |
| `POSTGRES_PASSWORD` | Postgres password. |
| `DJANGO_SECRET_KEY` | Django secret key. |
| `YIVI_TOKEN` | Yivi server token. |
| `SENTRY_DSN` | Sentry DSN for error reporting. |
| `SAML_PRIVATE_KEY` | Full PEM of the SAML SP private key. |
| `SAML_PUBLIC_CERT` | Full PEM of the SAML SP public certificate. |
| `SENTRY_AUTH_TOKEN` | Sentry integration token with `project:releases` scope (used by deploy to mark the release as deployed). |

### Environment variables (not secret)

| Variable | Example | Purpose |
| --- | --- | --- |
| `DEPLOY_DIR` | `/opt/tosti` | Where the compose stack lives on the VM. |
| `DEPLOY_HOST` | `tosti.vm.science.ru.nl` | VM's direct hostname; used by Caddy for the vhost redirect `tosti.vm → tosti`. |
| `DJANGO_HOSTNAME` | `tosti.science.ru.nl` | Public hostname served by Caddy for the Django app. |
| `YIVI_HOSTNAME` | `yivi.tosti.science.ru.nl` | Public hostname served by Caddy for the Yivi server. |
| `DJANGO_ALLOWED_HOSTS` | `tosti.science.ru.nl` | Django's `ALLOWED_HOSTS`. |
| `SAML_ENTITY_ID` | `tosti.science.ru.nl` | SAML entity ID. |
| `EMAIL_HOST` | `smtp.science.ru.nl` | SMTP server. |
| `EMAIL_PORT` | `25` | SMTP port. |
| `EMAIL_ADDRESS` | `www-tosti@science.ru.nl` | From/sender address; used for `EMAIL_HOST_USER`, `EMAIL_DEFAULT_SENDER`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`. |
| `SENTRY_ORG` | `tosti` | Sentry organization slug (used by deploy to create the release). |
| `SENTRY_PROJECT` | `tosti` | Sentry project slug (used by deploy to create the release). |

## What the workflow does

Runs directly on the VM via the self-hosted runner:

1. Checks out the commit that passed CI.
2. Writes SAML key/cert from secrets into `$DEPLOY_DIR/saml/`.
3. Copies `docker-compose.yml` and `Caddyfile` from the repo into `$DEPLOY_DIR/`.
4. Writes `$DEPLOY_DIR/.env` (mode 600) from the Environment's secrets and vars.
5. Runs `docker compose pull && docker compose up -d --remove-orphans`.
6. Polls `docker inspect` until the `web` container reports `healthy`; fails the job if it doesn't within ~5 minutes.

## Releases and image tags

The CI image gets tagged by source:

| Source | Tags applied |
| --- | --- |
| Push to `master` | `sha-<40-char-sha>`, `latest` |
| Published release `v1.2.3` | `sha-<40-char-sha>`, `1.2.3`, `1.2`, `1`, `latest` (unless pre-release) |
| Published pre-release `v1.2.3-rc1` | `sha-<40-char-sha>`, `1.2.3-rc1`, `1.2`, `1` (no `latest`) |

To cut a release: on GitHub → Releases → "Draft a new release" → create a new tag `vX.Y.Z` targeting `master` → click "Generate release notes" → publish. CI picks up the `release: published` event, runs test + lint, and pushes the image with the semver tags. The `:latest` tag moves forward too, so the next auto-deploy picks up the released build.

Deploys still trigger from master pushes only — releases don't trigger an extra deploy, they just add stable tags for rollback.

## Rollback

Every build is published with an immutable `sha-<commit-sha>` tag, and every release adds semver tags (`1.2.3`, `1.2`, `1`). To roll back:

```bash
ssh jdoesburg@<vm>
sudo -iu deploy-tosti
cd /opt/tosti
# Edit docker-compose.yml to pin a previous image. Prefer a semver tag if available:
#   image: ghcr.io/kioui/tosti:1.2.3
# Or an exact commit:
#   image: ghcr.io/kioui/tosti:sha-abc123...
docker compose up -d
```

## Security notes

- The runner executes any code that lands on `master`. Branch protection on `master` + required reviewers on the `tosti.science.ru.nl` Environment are the main defenses.
- Never set "Run workflows from fork pull requests" without approval — a malicious PR could exfiltrate secrets or run commands on the VM.
- The `github-runner` user should not have sudo. If it needs elevated privileges for something specific, use a tightly scoped sudoers rule.