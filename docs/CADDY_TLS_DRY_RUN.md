# Caddy TLS Dry Run

This procedure validates the OAE gateway against the **Let's Encrypt staging ACME directory**. Staging certificates are intentionally untrusted by browsers, but they exercise the same HTTP-01 reachability and account-registration flow while avoiding production certificate-rate limits.

## Preconditions

Run this only on an isolated host with Docker Compose, a disposable public DNS name, and inbound TCP ports 80 and 443. Point the DNS name at the host before starting Caddy. Do not reuse the production `API_DOMAIN`, production database, or production secrets.

Prepare a protected staging environment file from the supplied template:

```bash
cd /srv/oae-core
cp .env.staging.example .env.production
chmod 600 .env.production
# Replace API_DOMAIN, CADDY_EMAIL, POSTGRES_PASSWORD, and API_KEY_PEPPER.
```

Run the database migration and then start the stack with the staging override. The override replaces only the gateway configuration; all application services keep the production topology.

```bash
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml run --rm migrate
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml config
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml up -d --build
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml logs -f gateway
```

An ACME staging issuance is successful when the gateway log reports a certificate obtained for the staging `API_DOMAIN`. Verify that Caddy, not the API service, is the only public listener and that the certificate is the expected staging certificate:

```bash
curl -vkI "https://${API_DOMAIN}/health"
openssl s_client -connect "${API_DOMAIN}:443" -servername "${API_DOMAIN}" -showcerts </dev/null
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml ps
```

The `curl -k` option is intentional: public clients do not trust Let's Encrypt staging certificates. Do not promote a staging certificate to production. Remove the isolated stack after verification:

```bash
docker compose -f docker-compose.production.yml -f docker-compose.staging.yml down
```

To request a production certificate later, switch back to `docker-compose.production.yml` alone and retain the same working public DNS and port-80/443 reachability.
