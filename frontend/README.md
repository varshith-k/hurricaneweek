# Hurricane Week Frontend

Next.js frontend for the Hurricane Week educational simulation.

## Local development

Install dependencies and create the local environment file:

```bash
npm install
cp .env.local.example .env.local
```

The frontend expects the FastAPI backend at:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
NEXT_PUBLIC_USE_MOCK=false
```

Set `NEXT_PUBLIC_USE_MOCK=true` to run the demo flow with mocked data, no backend required.

Start the dev server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Stack

Next.js 16 (App Router), React 19, Tailwind CSS, TypeScript.

## Deployment

Deployed on DigitalOcean App Platform alongside the backend; see [`.do/app.yaml`](../.do/app.yaml) at the repo root. Not deployed on Vercel.
