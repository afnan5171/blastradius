# Delivery phases

Each phase receives a commit and the available checks. Docker requires a running daemon; local Python/Node checks substitute when unavailable.

- [x] 1. Repository, backend, frontend, database, Docker
- [x] 2. Account and relationship CRUD
- [x] 3. NetworkX graph engine
- [x] 4. React Flow visualization
- [x] 5. Compromise simulation
- [x] 6. Blast Radius scoring
- [x] 7. Recommendations and choke points
- [x] 8. Demo profile
- [x] 9. Design and accessibility
- [x] 10. Tests and documentation

## Final verification

15 backend tests, 4 frontend tests, Next.js production build, production HTTP smoke, and Docker Compose configuration validation passed. Browser simulation, editing, and reload persistence verified. Docker/PostgreSQL runtime remains unverified because the Docker daemon was stopped; see VALIDATION.md.
