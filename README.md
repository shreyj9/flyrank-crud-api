# FlyRank Task API — Postgres, Docker, and Supabase Auth

A FastAPI backend that combines the earlier task CRUD work with **Supabase authentication**. The project now supports sign up, login, logout, public routes, reusable bearer-token protection, Swagger authorization, PostgreSQL persistence, and one-command startup through Docker Compose.

## Assignment progression

```text
BE-01: Task CRUD with in-memory storage
BE-02: Same CRUD API with SQLite persistence
BE-04: Same CRUD API with Postgres and Docker Compose
BE-03: Supabase Auth, JWT verification, protected routes, and Swagger bearer auth
```

The task routes and Postgres repository remain available. Authentication is added in separate modules so passwords are never stored or hashed by this API.

## Architecture

```text
Client credentials → Supabase Auth → access token (JWT)
Client request + Bearer token → FastAPI auth dependency → Supabase token verification
FastAPI task routes → database.py repository → Postgres container → Docker volume
```

## Requirements

- Docker Desktop with Docker Compose
- A free Supabase project
- Git

## Supabase project setup

1. Create a Supabase project.
2. Open the project's API settings and copy the project URL and the public anon/publishable key.
3. Do **not** use a `service_role` or secret key.
4. For this practice assignment, turn off email confirmation under the Email authentication provider so a new test user can log in immediately.

## Environment variables

Copy the example file:

```bash
cp .env.example .env
```

Edit only the git-ignored `.env` and replace these two placeholders:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-or-publishable-key
```

The full environment file also contains the local Postgres configuration:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` | Local Postgres user |
| `POSTGRES_PASSWORD` | Local development password |
| `POSTGRES_DB` | Local database name |
| `DATABASE_URL` | Postgres connection string used by `database.py` |
| `API_PORT` | Host port for FastAPI |
| `SUPABASE_URL` | Public Supabase project URL |
| `SUPABASE_KEY` | Public anon/publishable key used by the Auth SDK |

Verify that the real `.env` is not tracked:

```bash
git check-ignore .env
git ls-files .env
```

The first command should print `.env`; the second should print nothing.

## Run the complete stack

```bash
docker compose up --build
```

Available pages:

- API root: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>

Stop the app and database while preserving the Postgres volume:

```bash
docker compose down
```

## Authentication endpoints

| Method | Endpoint | Authentication | Purpose | Success |
|---|---|---|---|---:|
| POST | `/auth/signup` | None | Create a Supabase user | 201 |
| POST | `/auth/login` | None | Return access and refresh tokens | 200 |
| POST | `/auth/logout` | Bearer JWT | End the current Supabase session | 204 |
| GET | `/public/info` | None | Public information | 200 |
| GET | `/protected/profile` | Bearer JWT | Return verified user metadata | 200 |
| GET | `/protected/dashboard` | Bearer JWT | Second route using the same auth dependency | 200 |

Missing email/password returns `400`. Missing or malformed bearer headers return `401` with:

```json
{"error":"Access token required"}
```

Tampered, expired, or invalid tokens return:

```json
{"error":"Invalid or expired token"}
```

## Task CRUD endpoints

| Method | Endpoint | Purpose | Success |
|---|---|---|---:|
| GET | `/tasks` | List Postgres tasks | 200 |
| GET | `/tasks/{task_id}` | Read one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update a task | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 |

## Curl authentication flow

Create a user:

```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

Log in:

```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

Copy `access_token` from the login response and call the protected profile:

```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer PASTE_ACCESS_TOKEN_HERE"
```

A valid token returns safe metadata such as the user's ID, email, and account creation time. Changing one token character returns `401`.

## Automated auth verification

With the stack running and email confirmation disabled:

```bash
./scripts/test_auth.sh
```

The script creates a unique practice account, logs in, checks the public route, proves a missing token is rejected, verifies the profile and dashboard, tampers with the token, and calls logout. It ends with:

```text
All Supabase authentication checks passed.
```

## Reusable security dependency

`auth_security.py` owns all bearer parsing and token verification. Protected routes use the same `get_current_user` dependency, so the route body runs only after Supabase verifies the JWT. Adding `/protected/dashboard` required no duplicated authentication logic.

## Swagger bearer authorization

FastAPI's `HTTPBearer` scheme creates the **Authorize** button and lock icons at `/docs`.

1. Run `POST /auth/login` in Swagger.
2. Copy the returned `access_token`.
3. Click **Authorize** and paste the token only.
4. Run `GET /protected/profile` and confirm status `200`.
5. Save the screenshot as `docs/auth-swagger.png`.

![Swagger UI with Supabase bearer authorization](docs/auth-swagger.png)

Detailed capture steps are in [`docs/auth-swagger-screenshot-steps.md`](docs/auth-swagger-screenshot-steps.md).

## Logout behavior

Supabase sign-out revokes the refresh session. An already-issued access-token JWT can remain valid until its expiry, which is why clients should delete their local tokens after logout and use short-lived access tokens.

## Main auth files

```text
auth_client.py       # reads SUPABASE_URL / SUPABASE_KEY and creates the SDK client
auth_models.py       # validates email and password request bodies
auth_service.py      # signup, login, token verification, logout
auth_security.py     # reusable bearer-token dependency and Swagger scheme
main.py              # auth, public, protected, and task routes
scripts/test_auth.sh # end-to-end authentication checks
```

## Assignment commit history

1. `Stage 0: setup server and supabase client`
2. `Stage 1: signup and login routes working`
3. `Stage 2: public route and unverified protected route`
4. `Stage 3: profile route token verification`
5. `Stage 4: auth dependency and logout endpoint`
6. `Stage 5: Swagger bearer auth and end-to-end checks`
7. `Stage 6: publish auth documentation`
