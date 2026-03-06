# ilm API (`apps/api`)

FastAPI service for TeacherOS.

## Story Scope

Implements identity + admin lifecycle baseline with:
- `POST /auth/login`
- `POST /auth/google`
- `POST /admin/organizations`
- `POST /admin/users/invite`
- `POST /admin/users/{user_id}/role`
- `POST /admin/users/{user_id}/membership`
- `PUT /admin/organizations/{org_id}/safety-controls`
- `GET /admin/organizations/{org_id}/safety-controls`
- `POST /admin/users/{user_id}/activate`
- `POST /admin/users/{user_id}/deactivate`
- `POST /admin/invitations/accept`
- `GET /admin/protected/organizations/{org_id}/summary`
- Generic invalid-credentials responses (anti-enumeration)
- JWT access token containing `sub`, `org_id`, and `role`
- Role-based home path in response
- In-memory organization creation, invitation onboarding, and user lifecycle transitions (`invited`, `active`, `deactivated`)

## Environment Variables

- `JWT_SECRET` (recommended; if omitted, API uses an ephemeral process-local secret)
- `JWT_ALGORITHM` (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXP_MINUTES` (default: `60`)
- `GOOGLE_OAUTH_CLIENT_ID` (required for real Google token verification)
- `GOOGLE_OIDC_JWKS_URL` (default: `https://www.googleapis.com/oauth2/v3/certs`)
- `GOOGLE_OIDC_ALGORITHM` (default: `RS256`)

Google callback/token-exchange integration should issue an ID token to the backend,
which is submitted to `POST /auth/google` as `id_token`.

Admin lifecycle endpoints require `Authorization: Bearer <token>` with a JWT role claim of `admin`.
Protected summary endpoint requires authenticated actor role of `admin` or `principal`, and actor org scope must match path org.
Safety controls mutation endpoint requires admin role and same-org scope; read endpoint requires same-org role of `admin`, `principal`, or `teacher` and returns latest versioned org defaults.

## Local Run

```bash
cd apps/api
python -m uvicorn app.main:app --reload
```

## Test

```bash
cd apps/api
pytest
```
