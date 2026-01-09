# trend-monitor Frontend

Next.js 14 frontend application for the trend-monitor system.

## Tech Stack

- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript 5
- **Styling:** TailwindCSS 3
- **State Management:** React Context API

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running (see backend/README.md)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your backend API URL:
```
NEXT_PUBLIC_API_URL=https://trend-monitor-production.up.railway.app
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js app router pages
│   ├── layout.tsx          # Root layout with AuthProvider
│   ├── page.tsx            # Login page
│   ├── dashboard/
│   │   └── page.tsx        # Dashboard page
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── AuthProvider.tsx    # Authentication context
│   └── LoginForm.tsx       # Login form component
├── lib/                    # Utility libraries
│   ├── api.ts              # API client
│   └── auth.ts             # Token management
└── public/                 # Static assets
```

## Authentication

The app uses JWT authentication with the following flow:

1. User enters credentials on login page
2. Frontend sends POST request to `/auth/login`
3. Backend returns JWT token
4. Token stored in localStorage
5. Token sent in Authorization header for protected routes
6. Dashboard accessible after authentication

### Bootstrap User

**Username:** `dave`
**Password:** `changeme123`

## Deployment

### Railway

1. Create new Railway service
2. Connect to this repository
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL=https://trend-monitor-production.up.railway.app`
4. Railway will automatically build and deploy

### Vercel

1. Import project to Vercel
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL=https://trend-monitor-production.up.railway.app`
3. Deploy

## Features

- ✅ Login page with username/password
- ✅ JWT token authentication
- ✅ Protected dashboard route
- ✅ Logout functionality
- ✅ Responsive design with TailwindCSS
- ✅ TypeScript for type safety

## Future Enhancements (Upcoming Epics)

- Epic 2: Data collection trigger UI
- Epic 3: Trending dashboard with Top 10 trends
- Epic 4: AI-powered trend brief UI
