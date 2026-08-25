# Production Secret Injection

## Purpose and safety boundary

`scripts/inject_production_secrets.py` is a **host-only assembly tool**. It combines the committed `.env.production.example` contract with seven values held in a protected, non-versioned source file: `API_DOMAIN`, `CADDY_EMAIL`, `POSTGRES_PASSWORD`, `API_KEY_PEPPER`, `SECRET_KEY`, `ALLOWED_HOSTS`, and `DATABASE_URL`.

The tool does not generate production secrets, call a cloud secret manager, start Docker, or enable governed build execution. It is intentionally compatible with any approved secret-management system that can materialize a mode-0600 temporary source file on the deployment host. Never commit, attach, paste, or upload that source file.

## Source-file contract

Create `/run/secrets/oae-production.env` through the host’s approved secret-management process. It must be a regular, non-symlink file with mode `0600` or stricter. Use a simple dotenv format with only single-line, Compose-safe values. The utility rejects empty values, placeholders, control characters, whitespace, dollar signs, hash signs, and other shell-sensitive characters. Use generated URL-safe secret values and a percent-encoded database URL if needed.

`ALLOWED_HOSTS` must be a compact JSON-style hostname list such as `["api.your-domain.example"]`; its required JSON quotes are the only quoted input form the utility accepts. The source must include all seven names. The tool validates names and syntax but never displays the values.

## Safe host sequence

First dry-run the source contract. The dry run creates no target file.

```bash
sudo install -d -m 0700 /etc/oae
sudo python3 scripts/inject_production_secrets.py \
  --source-file /run/secrets/oae-production.env \
  --target-file /etc/oae/.env.production \
  --dry-run \
  --report /var/lib/oae-evidence/secret-injection-dry-run.json
```

After reviewing the PASS report, assemble the target. The utility refuses to overwrite an existing target unless `--replace` is supplied, and it refuses to replace an insecure file or a symlink. It writes via an atomic same-directory replacement and sets mode `0600`.

```bash
sudo python3 scripts/inject_production_secrets.py \
  --source-file /run/secrets/oae-production.env \
  --target-file /etc/oae/.env.production \
  --report /var/lib/oae-evidence/secret-injection.json
```

Run the two existing validations immediately afterwards. Do not print the assembled target file.

```bash
sudo python3 scripts/check_environment_placeholders.py \
  --env-file /etc/oae/.env.production \
  --report /var/lib/oae-evidence/environment-placeholder-preflight.json

sudo python3 scripts/staging_preflight.py \
  --env-file /etc/oae/.env.production \
  --stage bootstrap \
  --expected-revision "$(git rev-parse HEAD)" \
  --report /var/lib/oae-evidence/staging-preflight.json
```

## Report boundary

The injection report includes the target path, action, seven variable names, and non-secret status. It does not include source values or target contents. Protect the report directory because host paths and deployment timing are operational metadata.

## References

[1] [Environment Placeholder Preflight](ENVIRONMENT_PLACEHOLDER_PREFLIGHT.md)

[2] [Production Template Placeholder Baseline](PRODUCTION_TEMPLATE_PLACEHOLDER_BASELINE_2026_08_25.md)
