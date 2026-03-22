# ilm — TeacherOS Monorepo

A full-stack EdTech platform with a FastAPI backend, React Native mobile app, and React admin web app.

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + PostgreSQL + MinIO (S3) |
| Mobile | React Native (Expo) |
| Admin Web | React + Vite |
| Infra | Docker Compose |

---

## Prerequisites

Install these before anything else:

| Tool | Version | Download |
|------|---------|----------|
| Node.js | >= 25 | https://nodejs.org |
| pnpm | >= 10 | `npm i -g pnpm` |
| Python | >= 3.11 | https://python.org |
| Docker Desktop | latest | https://docker.com/products/docker-desktop |
| Android Studio | latest | https://developer.android.com/studio (for mobile) |

> **Windows users:** open PowerShell as Administrator and run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

---

## 1. Clone & Install

```bash
git clone <repo-url>
cd ilm
pnpm install
```

---

## 2. Environment Setup

Copy the example env file (or create `.env.local` manually):

```bash
cp .env.local.example .env.local   # if it exists
```

Or create `.env.local` at the repo root with:

```env
JWT_SECRET=change-me-before-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXP_MINUTES=60

DATABASE_URL=postgresql+asyncpg://ilm:ilm@postgres:5432/ilm
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ilm-assignments

EMAIL_PROVIDER=console
JOB_PROVIDER=background_tasks
NOTIFICATION_PROVIDER=console
```

> These values match the `docker-compose.yml` defaults and work out of the box locally.

---

## 3. Start the Backend (API + DB + Storage)

```bash
docker compose up
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **MinIO** (S3-compatible storage) on `localhost:9000` (UI at `localhost:9001`)
- **API** (FastAPI) on `localhost:8000`
- **Worker** (background job processor)

API docs available at: `http://localhost:8000/docs`

---

## 4. Run the Admin Web App

In a new terminal:

```bash
cd apps/admin-web
pnpm dev
```

Opens at `http://localhost:5173`

---

## 5. Run the Mobile App (Android Emulator)

### 5a. Android SDK setup (first time only)

1. Open **Android Studio** → Device Manager → create a virtual device (API 34 recommended)
2. Set `ANDROID_HOME` in PowerShell (as Admin):
   ```powershell
   [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LOCALAPPDATA\Android\Sdk", "User")
   [System.Environment]::SetEnvironmentVariable("Path", "$env:Path;$env:LOCALAPPDATA\Android\Sdk\platform-tools;$env:LOCALAPPDATA\Android\Sdk\emulator", "User")
   ```
3. Restart your terminal

### 5b. Set the API URL

In `apps/mobile/app.json`, set `extra.apiBaseUrl` to your machine's IP:

- **Android emulator:** `http://10.0.2.2:8000` (already set)
- **Physical device / different machine:** `http://<your-local-ip>:8000`

### 5c. Create `local.properties` (first time only)

```bash
echo "sdk.dir=C\:\\Users\\<YOUR_USERNAME>\\AppData\\Local\\Android\\Sdk" > apps/mobile/android/local.properties
```

Replace `<YOUR_USERNAME>` with your Windows username.

### 5d. Boot the emulator

Start your AVD from Android Studio → Device Manager, wait for it to fully boot, then:

```bash
cd apps/mobile
pnpm android
```

> First build takes 5–15 minutes as Gradle downloads dependencies. Subsequent builds are fast.

---

## Project Structure

```
apps/
  api/          # FastAPI backend (Python)
  mobile/       # React Native + Expo (iOS/Android)
  admin-web/    # React + Vite admin dashboard
packages/
  contracts/    # Shared TypeScript types
  ui/           # Shared UI components (Tamagui)
  design-tokens/
  tsconfig/
infra/
  docker/       # Dockerfiles
```

---

## Common Commands

```bash
# Install all workspace dependencies
pnpm install

# Run all apps in parallel (web + mobile dev servers)
pnpm dev

# Lint / typecheck / test everything
pnpm lint
pnpm typecheck
pnpm test

# Backend only
docker compose up

# Mobile only
cd apps/mobile && pnpm android   # Android
cd apps/mobile && pnpm ios       # iOS (macOS only)

# Admin web only
cd apps/admin-web && pnpm dev
```

---

## API Reference

Full docs at `http://localhost:8000/docs` when the backend is running.

Key endpoints:
- `POST /auth/login` — email/password login
- `POST /auth/google` — Google OAuth login
- `POST /admin/organizations` — create org (admin)
- `POST /admin/users/invite` — invite user (admin)
- `POST /courses/drafts/generate` — AI course generation (teacher)
- `POST /grading/assignments` — create assignment (teacher)
