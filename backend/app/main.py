from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="trend-monitor API",
    description="Quantified trend monitoring system API",
    version="1.0.0"
)

# CORS Middleware (configure for frontend origin)
# Note: HTTPSRedirectMiddleware removed - Railway handles HTTPS termination
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with Railway frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response


@app.get("/")
async def root():
    return {"message": "trend-monitor API", "status": "operational"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and monitoring services"""
    return {
        "status": "healthy",
        "service": "trend-monitor-api",
        "version": "1.0.0"
    }
