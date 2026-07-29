# CGV Agent Console frontend

React/Vite frontend for the existing Python agent and CGV backend. It runs on
`http://127.0.0.1:5173`; the FastAPI backend runs on port `8000`.

## Run locally

Open two terminals.

Terminal 1 — backend:

```bash
cd starter_v0
pip install -r requirements.txt
CGV_WEB_COOKIE_SECURE=false CGV_WEB_ALLOWED_ORIGINS=http://127.0.0.1:5173 CGV_AGENT_PROVIDER=openai uvicorn web.cgv_api:app --reload
```

Set the selected provider's API key in `starter_v0/.env` first. `CGV_AGENT_MODEL`
is optional. `CGV_WEB_COOKIE_SECURE=false` is only for local HTTP development;
use HTTPS and its secure default in deployment.

Terminal 2 — frontend:

```bash
cd FE
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The browser calls `/api/chat`, `/api/cgv/login`, `/api/cgv/profile`, and
`/api/cgv/logout` through the backend. It only receives an opaque HttpOnly
session cookie; no CGV token is sent to or stored in the frontend.
