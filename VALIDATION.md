# Validation report

Validated during implementation on October 24, 2026.

## Automated checks

- **15 Pytest tests passed.** Health, account CRUD, relationship creation/deletion, duplicate handling, cross-user isolation, rejected unknown/oversized fields, session cookie attributes, directed traversal, shortest paths, parallel edges, isolated nodes, risk bounds, score bands, MFA and passkey reductions, relationship weights, circular recovery groups, choke points, deterministic recommendations, and demo simulation.
- **4 Vitest / Testing Library tests passed.** Simulation and reset, account metadata/MFA submission, connection direction and self-link prevention, and failed-save feedback.
- **Next.js production build passed**, including TypeScript validation and static page generation.
- **Production HTTP smoke passed.** The built Next.js server returned HTTP 200, proxied authenticated API requests, set a working session cookie, loaded ten demo accounts, and returned Gmail's nine affected accounts, score 79, and three recommendations.
- **Docker Compose configuration validated** with `docker compose config --quiet` and a placeholder validation password. No secrets were committed.

## Browser checks

Used the running Next.js frontend and FastAPI backend through the same-origin proxy:

1. Opened an empty session and loaded the ten-account, twelve-connection demo.
2. Simulated Gmail: nine affected accounts, four high-value accounts, seven direct and two indirect paths, score 79/100 (High), three recommendations.
3. Inspected graph highlighting and used Fit View to show the complete directed map.
4. Reloaded and confirmed all ten accounts and twelve relationships persisted.
5. Edited Gmail's fictional passkey metadata; the saved score fell from 79 to 40.
6. Restored the fictional demo settings; the score returned to 79.
7. Inspected the responsive narrow-desktop layout and saved `docs/dashboard.png`.

## Verification limits and development adjustments

- Docker Desktop's daemon was unavailable. The Compose stack, container image build, PostgreSQL execution, and PostgreSQL-specific concurrency lock were **not runtime-tested**. Local/API tests used SQLite through the same SQLAlchemy models. Docker remains the documented PostgreSQL path.
- Browser inspection used the available 739-pixel-wide in-app viewport. Full desktop and physical mobile devices were not separately tested.
- File watching hit the host's `EMFILE` limit. `WATCHPACK_POLLING=true` resolved local development preview; production mode did not need a watcher.
- The first test invocation lacked a backend import path; repository `pytest.ini` fixes it. Dependency install's initial ignored-build check was resolved by explicitly allowing esbuild in `pnpm-workspace.yaml`.
- Pytest emits a non-failing Starlette warning that its httpx integration is deprecated. All API assertions pass.
- Source was formatted with Prettier and Black. Each delivery phase has a descriptive Git commit; final checks cover the integrated application. Early phases used available targeted tests and framework builds, not a running Docker stack.

Preview processes were used only for validation. Start the application using README instructions.
