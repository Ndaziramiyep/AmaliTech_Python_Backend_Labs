# Gateway

The recommended front door for client traffic in this URL-shortener
microservices split — the only place that verifies a JWT (via
`auth_request`) and applies CORS. auth, shortener, and analytics each also
publish their own host port (`8001`-`8003`), but bound to `127.0.0.1` only
and strictly for local debugging — see below for why that bypasses this
gateway's auth/CORS entirely and must never carry real client traffic.
Service-to-service calls (the shortener→analytics click-event delivery, the
analytics→shortener ownership lookup) deliberately do not go through here
either — see [Service-to-service traffic](#service-to-service-traffic).

This is a plain `nginx:alpine` image (see the `gateway` service in
`services/docker-compose.yml`) configured by the single file in this
folder — `nginx.conf` — using the official image's built-in
`/etc/nginx/templates/*.template` `envsubst` mechanism. Compose bind-mounts
it into the container as `/etc/nginx/templates/default.conf.template` (not
`nginx.conf.template`) specifically so the generated file lands at
`/etc/nginx/conf.d/default.conf`, replacing the base image's own demo server
block on `:80` instead of running alongside it as a second, competing one.
There's no custom Dockerfile for it, and no other config file in this
folder.

## Routing table

| Path prefix                                                 | Routed to      | Gated by `auth_request`? |
|--------------------------------------------------------------|----------------|--------------------------|
| `/api/v1/auth/`                                               | auth           | No — this is how you get a token |
| `/api/v1/docs/<service>/`, `/api/v1/schema/<service>/`        | that service   | No                       |
| `/api/v1/urls/`                                               | shortener      | Yes                      |
| `/api/v1/analytics/`                                          | analytics      | Yes                      |
| `/api/v1/internal/`, `/internal/`                             | —              | Blocked (404) — see below |
| `/health`                                                     | —              | No — nginx's own liveness check, doesn't reach any backend |
| `/api/v1/` (everything else — resolve)                        | shortener      | No                       |
| `/` (the short link itself, e.g. `/abc123`)                    | shortener      | No                       |

`/health` here is unrelated to each service's own `GET /health/` (checked
directly by that service's own container healthcheck, not through this
gateway) — this one only proves nginx itself is up.

Backend hostnames (`auth`, `shortener`, `analytics`) are resolved per
request via Docker's embedded DNS (`resolver 127.0.0.11`) combined with
`set $var http://service:port; proxy_pass $var...;`, rather than once at
nginx startup — so a container recreated independently mid-run doesn't
leave nginx proxying to a stale IP.

## Centralized authentication (`auth_request`)

Before, shortener and analytics could each verify a caller's JWT
themselves, independently, on every request. This gateway instead verifies
it once, here, using nginx's `auth_request` module:

1. A request to a protected location (`/api/v1/urls/`, `/api/v1/analytics/`)
   triggers an internal subrequest to `/internal/verify`.
2. That subrequest proxies to auth's `GET
   /api/v1/auth/internal/token/validate/` — forwarding the client's
   `Authorization` header, plus the shared `X-Internal-Token` secret nginx
   itself attaches (`auth_request` subrequests carry headers but never a
   body, so the token travels as `Authorization: Bearer <token>`, not JSON).
3. Auth returns 401/403 for anything invalid, or 200 with the identity
   claims as response headers (`X-User-Id`, `X-Username`, `X-User-Tier`,
   `X-User-Is-Premium`) for a valid token.
4. `auth_request_set` captures those headers into nginx variables, which
   are then forwarded to the upstream via `proxy_set_header` — replacing
   whatever the original client sent under those same header names, so a
   client can't forge its own identity headers.

A 401/403 from the subrequest short-circuits the whole request via
`error_page 401 403 = @unauthorized`, returning a small JSON body before the
request ever reaches shortener or analytics.

## Service-to-service traffic

The shortener→analytics click-event delivery and analytics→shortener
ownership lookup are not proxied here either — they call each other
directly, container-to-container, over the same internal Docker network
(`http://shortener:8000`, `http://analytics:8000`; see each service's
`SHORTENER_SERVICE_URL`/`ANALYTICS_SERVICE_URL`). They're authenticated with
the shared `X-Internal-Token`/`X-Internal-Key` header (checked by each
service's own internal-only permission class) rather than a user's JWT, so
they gain nothing from this gateway's `auth_request` check — routing them
through here too would just be an extra hop. `/api/v1/internal/` and
`/internal/` are explicitly blocked (404) at the gateway rather than left to
fall through to some other service's routes by accident.

## CORS (frontend interaction)

All client traffic goes through this one gateway on one origin, so a
browser frontend served from a different origin — a React dev server on
`localhost:3000`, say — needs this gateway to answer with CORS headers, not
each Django service individually. That's implemented once, here, rather
than adding `django-cors-headers` to every Python service — the same
centralization rationale as JWT verification above.

`add_header 'Access-Control-Allow-Origin' '${CORS_ALLOWED_ORIGIN}' always;`
(plus `Allow-Credentials`, `Allow-Methods`, `Allow-Headers`,
`Expose-Headers`) is set once at server level in `nginx.conf`, so every
location inherits it automatically — proxied responses included, and
`always` means it's attached regardless of the upstream's status code
(401s from `auth_request`, 5xxs, everything). `CORS_ALLOWED_ORIGIN` is
substituted the same way `INTERNAL_SERVICE_TOKEN` already is (the
`envsubst` template mechanism — see the top of this README), defaulting to
`http://localhost:3000`.

One static origin, not `*`. Once `Allow-Credentials: true` and
`Authorization` are in play, a wildcard origin is unsafe (and browsers
reject it outright for credentialed requests) — reflecting exactly one
configured origin is the correct minimal version of this. A real deployment
fronting more than one origin would swap this for a
`map $http_origin $cors_origin { ... }` allowlist instead of a single
static value.

**The OPTIONS preflight problem.** A browser's CORS preflight is a plain
`OPTIONS` request with no `Authorization` header. On the two
`auth_request`-gated locations (`/api/v1/urls/`, `/api/v1/analytics/`),
that would hit `auth_request` and come back 401 before the browser ever
gets the green light to send its real request — so each of those two
locations short-circuits `OPTIONS` with `return 204;` before `auth_request`
runs. The other locations (`/api/v1/auth/`, the resolve/redirect
catch-alls) don't need this: nothing gates them, so the preflight reaches
the upstream Django service, whose default DRF `OPTIONS` handling already
answers 200, and the server-level `add_header ... always` still attaches to
that response.

To point this at a real frontend, set `CORS_ALLOWED_ORIGIN` in
`gateway/.env` to that origin (scheme + host + port, no trailing
slash — exactly what the browser sends as `Origin`) and restart the gateway
container (or `docker compose up -d gateway` from `services/` to re-render
the template).

## Known simplification

Docs/schema aren't multiplexed under a single path for each service the way
`/api/v1/urls/`, etc. are — each service's own drf-spectacular Swagger UI
assumes it's the only thing on the host, so all three define docs at the
same literal `/api/v1/docs/` path. The `/api/v1/docs/<service>/` and
`/api/v1/schema/<service>/` routes work around that with a rewrite, but a
generated schema that references other absolute paths (rare, but possible)
could still point at the wrong place. A real deployment fronting a browser
client heavily would give each service its own subdomain instead.

## Configuration

Copy `.env.example` to `.env` in this folder before starting the stack:

```bash
cp gateway/.env.example gateway/.env
```

- `INTERNAL_SERVICE_TOKEN` must be identical to auth-service's own
  `INTERNAL_SERVICE_TOKEN` (`services/auth-service/.env`) — it's what this
  gateway sends on the `/internal/verify` subrequest, and what
  `IsInternalGateway` checks on the receiving end.
- `CORS_ALLOWED_ORIGIN` defaults to `http://localhost:3000`; point it at
  your real frontend origin as described above.
