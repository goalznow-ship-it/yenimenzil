# Deployment Documentation

This file is kept for backward compatibility with CI references. The
authoritative deployment guide is at the repository root:

- [../DEPLOYMENT.md](../DEPLOYMENT.md)

The production stack uses **Caddy** as the reverse proxy (see
`deploy/Caddyfile`), not nginx. The former nginx-based deployment docs and
`docs/nginx.conf` were removed as stale in Phase 13.