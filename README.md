# trend-monitor

Quantified trend monitoring system that predicts high-impact content opportunities through cross-platform signal convergence.

## Project Overview

This system enables content teams to detect cross-platform trend momentum by collecting data from multiple sources (Reddit, YouTube, Google Trends, SimilarWeb) and calculating a Cross-Platform Momentum Score.

## Tech Stack

- **Backend:** Python 3.10+ with FastAPI
- **Database:** PostgreSQL 14+ (managed by Railway)
- **Frontend:** Next.js with TypeScript
- **Deployment:** Railway platform

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or use Railway managed database)
- Node.js 18+ (for frontend)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp backend/.env.example backend/.env
```

### Run Backend Locally

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/health

## Deployment

This project is configured for automatic deployment to Railway:

1. Push to GitHub main branch
2. Railway auto-deploys backend
3. Railway provisions managed PostgreSQL

## Project Structure

```
trend-monitor/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py   # FastAPI application entry point
│   │   ├── config.py # Configuration management
│   │   └── api/      # API endpoints
│   └── requirements.txt
├── frontend/         # Next.js frontend (coming in Story 1.4)
└── README.md
```

## License

MIT
