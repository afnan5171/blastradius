# BlastRadius

**If this account gets hacked, what else could an attacker reach?**

BlastRadius is a local-first consumer cybersecurity MVP. Build a manual map of your online accounts, simulate one account being compromised, and see understandable paths to other accounts plus prioritized security improvements. No external accounts are scanned or accessed.

## Quick start with Docker

Prerequisites: Docker Desktop (running) with Docker Compose. From this directory:

```sh
cp .env.example .env
# Edit .env: replace POSTGRES_PASSWORD with a random URL-safe value.
# Example generator: python3 -c 'import secrets; print(secrets.token_hex(24))'
docker compose up --build
```

Open **http://localhost:3000** and choose **Explore demo profile**. The app creates a private browser demo session. Select Gmail and click **Simulate Compromise**. Alternatively, add your own accounts and directed connections.

PostgreSQL uses a named volume, so `docker compose down` preserves your data. Do not add `-v` unless you intend to erase the database. Only the frontend port is published, bound to loopback; database credentials stay in the backend environment. Keep the password URL-safe because Compose inserts it into the database URL.

Run tests inside the stack:

```sh
docker compose run --rm backend python -m pytest tests -q
docker compose run --rm frontend pnpm test
```

## Local development without Docker

Requires Python 3.12+ and Node.js 22+, plus pnpm 11.25.0 (`corepack enable`, then `corepack prepare pnpm@11.25.0 --activate`).

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Visit http://127.0.0.1:3000. The Next.js server proxies `/api/*` to FastAPI. The fallback database is a persistent SQLite file in the backend working directory. For local PostgreSQL set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/blastradius` before starting FastAPI. Docker always uses PostgreSQL.

If macOS reports `EMFILE: too many open files, watch`, use `WATCHPACK_POLLING=true pnpm dev`. Keep the same hostname to retain the demo cookie. If port 3000 changes, use the printed development URL. Interactive API documentation is available at http://127.0.0.1:8000/docs; authenticate with `POST /auth/demo` there before using protected endpoints on that host.

Build and test from the repository root:

```sh
.venv/bin/python -m pytest -q
cd frontend
pnpm test
pnpm build
pnpm start
```

Do not run a development server and production build against the same `.next` directory simultaneously. Stop the dev server before building.

## Features

- Validated account create, read, update, and delete, with 11 categories and four importance levels.
- Directed connections with 11 relationship types, configurable weights, duplicate checks, notes, and deletion.
- Interactive React Flow graph: draggable nodes, pan, zoom, arrows, connection labels, security indicators, and automatic initial placement.
- Safe compromise simulations: direct and indirect exposure, shortest paths, relationship explanations, affected counts, and high-value counts.
- Documented 0–100 exposure score and deterministic top-three recommendations.
- Dependency hubs, out-degree centrality, and circular recovery group detection.
- Browser-isolated demo sessions, persistent metadata, ten-account demo, responsive forms, and privacy messaging.

Recovery email/phone fields are descriptive metadata. **They do not create graph edges automatically.** Add a connection separately. `Gmail → Amazon` means Gmail grants a route into Amazon. Shared-password links are also directed; add the reverse connection if you want to model exposure in both directions.

## Architecture

```text
frontend/                 Next.js + React + TypeScript + Tailwind CSS
  app/                    Dashboard, styling, layout
  components/             React Flow map and accessible form dialogs
  lib/types.ts            REST client and shared frontend types
  tests/                  Vitest + Testing Library behavior tests
backend/
  app/
    main.py               Application lifecycle and browser safety middleware
    auth.py               Opaque demo-session authentication
    db.py, models.py       SQLAlchemy persistence
    schemas.py            Pydantic input validation and weights
    routes.py             Account and relationship CRUD + ownership checks
    graph.py              Pure NetworkX analysis and recommendations
    analysis_routes.py    Authenticated analysis REST endpoints
    demo.py               Non-destructive, empty-profile-only demo seed
  tests/                  Pytest API and graph coverage
docker-compose.yml        Next.js → FastAPI → PostgreSQL
TODO.md                   Phase completion checklist
VALIDATION.md             Verification evidence and limits
```

The graph uses `MultiDiGraph` to preserve different relationships between the same accounts. Shortest attack paths minimize hop count, selecting the highest-weight relationship if multiple edges connect a pair. The score separately considers the strongest weighted path to each destination. Recovery-loop detection uses strongly connected components rather than enumerating every cycle, keeping analysis bounded for the MVP profile limit of 100 accounts and 500 connections.

## Scoring

The score is an **exposure-priority heuristic, not a probability of compromise**. The starting account is excluded from affected counts. A zero score means no other account is reachable in the current map, not that the starting account is safe.

For each reachable destination:

```text
impact = importance × category multiplier × destination protection × strongest path strength
importance: Low=1, Medium=2, High=3, Critical=4
category: Financial=1.5, Cloud Storage=1.25, Password Manager=1.75, other=1
protection: MFA ×0.75; passkey ×0.5; combined ×0.375
path strength: product of relationship weights / 10 along the strongest path
score = round((85 × (1 − exp(−sum(impact)/14)) + 15 × source out-degree centrality)
              × source protection)
```

The final score is clamped to 0–100. Low: 0–20; Moderate: 21–40; Elevated: 41–60; High: 61–80; Critical: 81–100.

Relationship defaults: password reset, shared password, and stored credential = 10; recovery email, Google/Apple sign-in, and OAuth write = 9; Facebook sign-in = 8; OAuth read = 6; phone recovery and Other = 5.

MFA/passkeys change prioritization but **never erase reachable paths**. Starting-account protection reflects prevention value even though the simulation asks what could follow a compromise. Intermediate-account controls are not compounded; the model is intentionally conservative. Scores do not account for service-specific recovery policies, session theft, or bypasses. Editable formula and constants are documented in `backend/app/graph.py`.

Recommendations are rule-based and stably ranked: recovery loops, shared passwords, missing passkeys/MFA, single recovery dependencies, sensitive accounts depending on weak accounts, and OAuth permissions. Dependency reach gives hub accounts extra priority. They are suggested actions, not verified remediation. Change settings in the actual service, then update the map.

## Example simulation

The fictional profile contains Gmail, Apple ID, Amazon, Instagram, PayPal, Dropbox, Steam, Discord, LinkedIn, and Password Manager, linked by 12 directed relationships.

Gmail reaches **9 other accounts**, including **4 high-value accounts**, through **7 direct** and **2 indirect** paths. The demo's score is **79 / 100 (High)**. For example:

- Gmail → PayPal: Password reset.
- Gmail → Discord → Steam: Google sign-in → Shared password.
- Gmail → Apple ID → Password Manager: Recovery email → Recovery email.

Gmail is the highest-priority choke point. The demo includes an Apple ID/Gmail recovery loop. These connections are illustrative metadata, not claims about the services' actual recovery implementations.

## REST API

All endpoints except `/health` and session creation require the HttpOnly session cookie. The UI uses the same-origin `/api` proxy.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/demo` | Create or reuse an isolated browser demo session |
| GET | `/auth/me` | Read current session identity |
| GET / POST | `/accounts` | List / create accounts |
| PUT / DELETE | `/accounts/{id}` | Update / delete an owned account |
| GET / POST | `/relationships` | List / create directed connections |
| DELETE | `/relationships/{id}` | Remove an owned connection |
| POST | `/simulate/{id}` | Calculate potential exposure and recommendations |
| GET | `/risk-scores` | Ranked account scores |
| GET | `/recommendations/{id}` | Top improvements for one account |
| GET | `/security-chokepoints` | Dependency hubs |
| GET | `/circular-dependencies` | Recovery groups with loops |
| POST | `/demo/load` | Seed an empty profile; existing data is never overwritten |

## Privacy and basic threat model

**BlastRadius never asks for or stores your account passwords.** Unknown request fields, including password fields, are rejected. Do not put secrets in free-text notes. Only account metadata and dependency information belong here.

Protected assets include service names, usernames, recovery contacts, the dependency graph, and session credentials. Metadata can still reveal sensitive personal information.

- API ownership checks prevent one browser session from reading or modifying another profile, including relationship endpoints and analysis.
- Random 256-bit session tokens are stored only as SHA-256 hashes in the database. Cookies are HttpOnly and SameSite=Strict. No passwords or external service authentication secrets are collected.
- Cross-site browser writes are rejected; cookies and same-origin proxying provide the browser session boundary. Input validation, enum constraints, length limits, parameterized ORM queries, and React text escaping reduce common injection risks.
- Responses use `Cache-Control: no-store`. The local Docker service binds to loopback and never publishes database/backend ports. `.env` and local databases are ignored by Git.
- Local HTTP uses `COOKIE_SECURE=false`. Any future hosted deployment requires HTTPS and `COOKIE_SECURE=true`, real authentication and account recovery, rate limits, secret management, backup policies, and a broader security review.
- An attacker controlling the browser session, host, or database can access the metadata. This MVP has no application-level database encryption, audit trail, session management UI, or automated retention cleanup. Deleted metadata may remain in backups.

Demo sessions expire after 30 days and cannot be recovered after the cookie is cleared or expires. This is a development login, not production account registration. `DEMO_LOGIN_ENABLED=false` disables new demo session creation; existing sessions remain usable until expiry. Do not expose this MVP publicly as-is.

## Screenshots

![Verified simulation map](docs/dashboard.png)

See `docs/dashboard.png` for the verified local preview. Additional planned screenshots: wide desktop dashboard, mobile account form, and a full simulation result.

## Current limitations

- Manual metadata only; no scanning, service verification, or live security changes.
- Lightweight deterministic initial graph layout; dragged positions reset after reload.
- Demo sessions are browser-specific; no cross-device identity or email/password login.
- Database tables are created at startup. Production schema changes need migrations; this is a fresh-install MVP.
- Analysis is conservative and cannot prove takeover or predict a breach.
- Docker/PostgreSQL runtime could not be exercised in the build environment because Docker Desktop's daemon was stopped. API tests and local preview used SQLite. See `VALIDATION.md`.

## Roadmap (not implemented)

Google OAuth integration; Microsoft integration; browser extension; automatic account discovery; breach intelligence; password manager integrations; mobile app; automated permission analysis. These features require explicit consent and a stronger production identity and security model before implementation.
