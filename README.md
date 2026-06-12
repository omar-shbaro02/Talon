# TALON

TALON is a full-stack MVP for an AI-native Coaching Intelligence Platform.

## Stack

- Frontend: React, Vite, Tailwind CSS via `@tailwindcss/vite`
- Backend: FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL first, SQLite fallback if `DATABASE_URL` is changed locally
- AI layer: modular OpenAI-backed agents with structured JSON fallbacks

## Run Everything

From the outer `Talon` directory:

```powershell
npm run dev
```

This starts FastAPI on `http://localhost:8000` and Vite on `http://localhost:5173`.

For the fastest local boot, the root dev runner uses `sqlite:///./talon_local.db`
unless `DATABASE_URL` is already set in your shell. To run against PostgreSQL,
set `DATABASE_URL=postgresql://postgres:password@localhost:5432/talon_db`
before `npm run dev`.

## Run Backend Only

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The requested default database URL is already in `backend/.env`:

```text
DATABASE_URL=postgresql://postgres:password@localhost:5432/talon_db
```

Create the `talon_db` database in PostgreSQL before running migrations. To use the local fallback instead, set:

```text
DATABASE_URL=sqlite:///./talon_local.db
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Calendar Invites

Client sessions generate Outlook-style calendar invitations. Without SMTP
settings, TALON creates an email draft link and downloadable `.ics` invite.
To send emails directly, set these in `backend/.env`:

```text
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@example.com
SMTP_USE_TLS=true
COACH_DISPLAY_NAME=Your Name
```

## Meeting Agent

TALON can send a visible Recall.ai bot named `TALON Assistant` into Zoom,
Google Meet, or Microsoft Teams meetings. Configure these backend variables:

```text
RECALL_API_KEY=
RECALL_WEBHOOK_SECRET=
PUBLIC_BACKEND_URL=http://localhost:8000
```

When `RECALL_API_KEY` is not set, the Meeting Agent page still stores the
meeting request and returns `configuration_required` instead of sending a bot.

## Google Calendar

TALON supports backend Google OAuth for scheduling sessions, creating Google
Calendar events, generating Google Meet links, and marking meetings as ready
for the TALON Meeting Agent.

Configure these backend variables in `backend/.env`:

```text
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar
FRONTEND_URL=http://localhost:5173
TOKEN_ENCRYPTION_KEY=
```

Generate `TOKEN_ENCRYPTION_KEY` with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Open `http://localhost:5173/settings` to connect Google Calendar, then use
`http://localhost:5173/schedule` to create Google Calendar sessions.

## Zoom And Microsoft Teams Meetings

TALON can generate Zoom and Microsoft Teams links from the Schedule dashboard
after backend API credentials are configured in `backend/.env`.

For Zoom, create a Server-to-Server OAuth app in the Zoom App Marketplace with
meeting creation permissions, then set:

```text
ZOOM_ACCOUNT_ID=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
ZOOM_USER_ID=me
```

For Microsoft Teams, create a Microsoft Entra app registration, add Microsoft
Graph application permission `OnlineMeetings.ReadWrite.All`, grant admin
consent, then create and grant an application access policy for the Teams host
user. Set:

```text
MICROSOFT_TENANT_ID=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
TEAMS_USER_ID=
```

`TEAMS_USER_ID` can be the host user's Microsoft object ID or UPN. For local
testing only, `TEAMS_ACCESS_TOKEN` can be supplied instead of Microsoft client
credentials, but the token will expire.

## MVP Capabilities

- Client workspaces with profile, goals, challenges, and AI coach analysis
- Meeting intelligence with summaries, topics, action items, decisions, observations, and follow-up email drafts
- Knowledge Hub for manual coaching notes and frameworks
- Content Studio for posts, outlines, exercises, articles, session plans, and email drafts
- Dashboard summary with active clients, pending actions, recent summaries, and recommendations
- Automation preview for future workflow orchestration
