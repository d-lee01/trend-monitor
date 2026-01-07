FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application
COPY backend /app/backend

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Change working directory to backend
WORKDIR /app/backend

# Start command (Railway sets PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
