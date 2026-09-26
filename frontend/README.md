# Hurricane Week Frontend

This is the Next.js frontend for the Hurricane Week educational simulation.

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

Start the development server:

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.


You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel
Set `NEXT_PUBLIC_USE_MOCK=true` to run the demo flow without the backend.
