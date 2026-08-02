# React Frontend for the RAG Backend — Plan

This is a living document — update it as the frontend grows or the plan changes, rather than
keeping the old plan around as history. Vishal is learning React hands-on, so this plan describes
*what* to build and *why*, broken into phases meant to be built (and reviewed) one at a time rather
than generated wholesale.

## Changelog

- **2026-08-02**: Added auth (login/register), roles (user/admin), and routing (login page +
  protected homepage chat) to the plan. Supersedes the earlier single-page-no-auth version below.

## Context

The backend (`backend/src/`) is a working FastAPI RAG service — PDF upload/ingestion, Qdrant
vector search, Gemini-based grounded answering with citations — exercised so far only via curl.
The frontend turns this into a real app with two roles:

- **user** — logs in, asks questions in a chat UI, sees cited answers.
- **admin** — everything a user can do, plus manages the document corpus (upload/delete).

There is currently **no auth of any kind** on the backend — no `User` model, no login endpoint, no
JWT verification, and none of the existing routes (`/upload`, `/ask`, `/documents`) check who's
calling. That's new work, not just a frontend concern — see "Backend changes needed" below.

## Roles & auth model

- Two roles only: `user` and `admin`. Stored as a field on the `User` row (e.g. an enum column),
  not a separate permissions table — no need for anything more granular right now.
- **Assumption to confirm**: document management (`/upload`, `DELETE /documents*`) becomes
  admin-only; asking questions (`/ask`, `GET /documents` to see what's indexed) is open to both
  roles. This mirrors "admin curates the corpus, users query it." Easy to change if the intent was
  different (e.g. every user manages their own documents).
- JWT-based auth: login returns a signed token; the frontend attaches it as
  `Authorization: Bearer <token>` on every API call; a backend dependency decodes and verifies it
  per-request. No refresh tokens / sessions for v1 — a single reasonably-long-lived access token
  (e.g. 24h) is enough for a learning project and keeps the frontend state simple.

## Backend changes needed (new work, not yet started)

1. **`models.py`** — add a `User` model: `id`, `email` (unique), `password_hash`, `role`
   (`user`/`admin`), `created_at`.
2. **Password hashing** — `passlib[bcrypt]` (or `bcrypt` directly) to hash on register, verify on
   login. Never store or log plaintext passwords.
3. **JWT issuing/verification** — `pyjwt` or `python-jose`. A `create_access_token(user)` helper
   and a `decode_access_token(token)` helper, secret key from `config.py`/env, not hardcoded.
4. **`routers/auth.py`** (new):
   - `POST /auth/register` — `{email, password}` → creates a `user`-role account (admin accounts
     are seeded/promoted manually for now, not self-service — avoids needing an "invite an admin"
     flow this early).
   - `POST /auth/login` — `{email, password}` → `{access_token, token_type, user: {id, email,
     role}}`.
   - `GET /auth/me` — returns the current user from the token; lets the frontend re-hydrate a
     session on page reload without re-sending credentials.
5. **Auth dependency** (e.g. `dependencies/auth.py`) — `get_current_user` (FastAPI
   `Depends`) that reads the `Authorization` header, verifies the JWT, loads the user, and 401s if
   missing/invalid/expired. A second dependency `require_admin` builds on it and 403s for
   non-admins. Applied to routers via `Depends(...)` — `ask.py` gets `get_current_user`,
   `upload.py`'s mutating routes get `require_admin`.
6. **CORS** — still needed (see below), and now also needs `allow_headers` to include
   `Authorization` explicitly if the CORS middleware config narrows headers.

This is a distinct, buildable-first chunk of work: get register → login → `/auth/me` working and
testable via curl *before* wiring the frontend to it.

## Frontend routes

Switched to react-router's **data router** API (`createBrowserRouter` + `<RouterProvider>`)
instead of `<BrowserRouter><Routes>`, and expanded from one protected page to a multi-page app
under a shared `AppLayout` (nav + `<Outlet/>`). `/login` sits outside `AppLayout` as its own
top-level route — a logged-out visitor shouldn't see the authenticated nav.

| Route | Access | Shows |
|---|---|---|
| `/login` | public | Login form + Register form (currently both shown at once, stateless — no toggle wired yet) |
| `/` (index) | protected (any logged-in role) | Home |
| `/chat` | protected (any logged-in role) | Chat UI against `/ask` |
| `/documents` | protected, **admin-only** | Document list (view/delete) |
| `/upload` | protected, **admin-only** | Upload form |
| `/settings` | protected (any logged-in role) | tbd |

Route guarding isn't wired yet — every route above is currently reachable by anyone. Once auth
exists, the data-router API lets guards live as `loader`s (`redirect()` before render) instead of
a `ProtectedRoute` wrapper component — decide which when Phase 3/4 gets there. Admin-only routes
(`/documents`, `/upload`) still need a role check somewhere (loader or in-component) once roles
exist.

## Frontend structure (current — see `src/` for the live version, this is a snapshot)

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx                 # <RouterProvider router={router} />
│   ├── app/
│   │   ├── router.tsx           # createBrowserRouter config: /login (top-level) + / (AppLayout,
│   │   │                        # with index/chat/documents/upload/settings as children)
│   │   └── AppLayout.tsx        # nav (Home/Chat/Documents/Upload/Settings) + <Outlet/>
│   ├── pages/
│   │   ├── LoginPage.tsx        # hosts LoginForm + RegisterForm
│   │   ├── Home.tsx / Chat.tsx / Documents.tsx / Upload.tsx / Settings.tsx  # placeholders so far
│   │   └── NotFound.tsx         # router's errorElement
│   ├── components/
│   │   ├── LoginForm.tsx        # stateless so far — no onChange/onSubmit yet
│   │   └── RegisterForm.tsx     # same
│   ├── context/                 # not built yet — AuthContext lands with Phase 3
│   ├── api/                     # not built yet — client.ts / auth.ts / documents.ts land as
│   │                            # each phase needs them
│   ├── types.ts                 # not built yet
│   └── App.css
```

## Phases (build and review one at a time)

1. **Backend auth** — `User` model + register/login/me endpoints + JWT dependency, tested via
   curl/Postman before any frontend work touches it.
2. **Routing skeleton** — add `react-router-dom`; `/login` and `/` routes with placeholder content,
   no real auth yet (fake a logged-in state to build the route guards and layout).
3. **Login/Register UI wired to the backend** — `AuthContext`, `api/auth.ts`, real
   `POST /auth/login` and `POST /auth/register` calls, token stored in `localStorage`, redirect to
   `/` on success.
4. **Protected homepage + chat** — `ProtectedRoute`, `ChatPanel` calling `POST /ask` with the
   `Authorization` header, session rehydration via `GET /auth/me` on page load/refresh.
5. **Admin document management** — `DocumentsPanel` shown only for `role === 'admin'`, upload/list/
   delete wired to the existing (now `require_admin`-protected) document endpoints.

Each phase should end in something runnable and demoable, not a half-wired feature spanning
multiple phases.

## API surface (existing + new)

| Action | Endpoint | Access | Notes |
|---|---|---|---|
| Register | `POST /auth/register` | public | new |
| Login | `POST /auth/login` | public | new — returns JWT |
| Current user | `GET /auth/me` | any authenticated role | new |
| Upload a PDF | `POST /upload` (multipart, field `file`) | admin | 409 if `content_hash` already exists |
| List documents | `GET /documents` | any authenticated role | `{documents: [{doc_id, filename, content_type, size_bytes, uploaded_at, chunks}]}` |
| Delete one document | `DELETE /documents/{doc_id}` | admin | 404 if missing |
| Delete all documents | `DELETE /documents` | admin | |
| Ask a question | `POST /ask` `{query, top_k?}` | any authenticated role | `{query, answer, sources: [...]}`, 502 if the LLM call fails |

## CORS (unchanged from before, still required)

`backend/src/main.py` has no CORS middleware yet, so the browser blocks calls to the API even
though it works via curl:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Behavior notes

- **Token storage**: `localStorage` (simplest for a learning project; note for later that this is
  vulnerable to XSS — an httpOnly cookie would be the production-grade choice, out of scope now).
- **401 handling**: `api/client.ts` catches 401 globally, clears the stored token/user, and
  redirects to `/login` — avoids repeating this check in every component.
- **Chat state**: still client-side only (`useState` turn history), no persistence across reloads —
  unchanged from the original plan.
- **Upload flow** (admin): pick file → POST → on success, refetch document list; surface 409/400
  `detail` messages inline instead of a generic error.
- **Delete**: per-document delete with a `confirm()` step; "delete all" gets the same.

## Verification (per phase)

1. Backend: `POST /auth/register`, `POST /auth/login`, `GET /auth/me` (with and without a valid
   token) all behave correctly via curl before touching the frontend.
2. Frontend: register a user → land on `/login` → log in → land on `/` → refresh the page and
   confirm the session survives (via `/auth/me`) → log out → confirm `/` redirects to `/login`.
3. Role check: log in as a seeded admin → confirm the documents panel appears and
   upload/delete work; log in as a plain user → confirm it's hidden and the admin-only endpoints
   403 if called directly.
4. Ask flow: as either role, ask a question → confirm the answer renders with numbered sources.

## Open questions / things to confirm

- Is "admin manages documents, everyone can ask questions" the right split, or should regular
  users also see/manage their own uploads?
- Admin accounts: fine to create the first one manually (e.g. a seed script or a one-off DB edit)
  rather than building admin-invite/promotion flows right now?
- Token lifetime: 24h access token with no refresh flow acceptable for now?
