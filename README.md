# ilm Monorepo Scaffold

This repository is initialized for the TeacherOS implementation plan using a Turborepo-style workspace layout.

## Story 1.1 Scope

This setup intentionally includes only scaffold and baseline task orchestration.
Feature development (auth, grading, messaging, analytics) starts in later stories.

## Required Tooling

- Node.js >= 25
- pnpm >= 10
- Python >= 3.11 (for `apps/api`)

## Install

```bash
pnpm install
```

## Workspace Commands

```bash
pnpm verify:scaffold
pnpm lint
pnpm test
pnpm typecheck
pnpm build
```

## Monorepo Layout

```text
apps/
  api/         # FastAPI service placeholder
  mobile/      # React Native/Expo placeholder
  admin-web/   # Admin web placeholder
packages/
  contracts/   # Shared contracts/types placeholder
```

## Handoff Notes

- Story 1.2 should start real app bootstrapping on top of this structure.
- Keep app/package names and paths stable to preserve architecture alignment.

## Auth Story Notes (1.2)

- API auth endpoint: `POST /auth/login` in `apps/api`.
- Local API env vars:
  - `JWT_SECRET`
  - `JWT_ALGORITHM` (default `HS256`)
  - `JWT_ACCESS_TOKEN_EXP_MINUTES` (default `60`)
- API docs: `apps/api/README.md`
