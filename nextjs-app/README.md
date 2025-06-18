# Emreq Frontend

A modern Next.js frontend for the Emreq AI Engineering Manager.

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: Railway-hosted Python FastAPI server
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth

## Features

- 🖥️ Terminal-style interface
- 🔐 Secure authentication with Supabase
- 💬 Real-time chat with AI engineering manager
- 👤 User profile management
- 📱 Responsive design
- ⚡ Fast deployment on Vercel

## Environment Variables

Required environment variables for deployment:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_API_URL=your_railway_backend_url
```

## Local Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Deployment

This app is designed to deploy on Vercel with zero configuration. The backend runs separately on Railway.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/emreq-frontend)
