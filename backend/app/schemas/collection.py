"""Pydantic schemas for collection endpoints."""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class CollectionResponse(BaseModel):
    """Response model for POST /collect endpoint."""
    collection_id: UUID = Field(..., description="Unique identifier for the collection run")
    status: str = Field(..., description="Current status: 'in_progress', 'completed', or 'failed'")
    started_at: datetime = Field(..., description="Timestamp when collection started")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "collection_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "in_progress",
                "started_at": "2026-01-09T10:30:00Z",
                "message": "Collection started. This will take approximately 20-25 minutes."
            }
        }


class CollectionStatusResponse(BaseModel):
    """Response model for GET /collections/{id} endpoint."""
    collection_id: UUID = Field(..., description="Unique identifier for the collection run")
    status: str = Field(..., description="Current status: 'in_progress', 'completed', or 'failed'")
    started_at: datetime = Field(..., description="Timestamp when collection started")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when collection completed (null if in progress)")
    trends_found: int = Field(..., description="Number of trends collected and stored")
    duration_minutes: float = Field(..., description="Duration of collection in minutes")
    errors: Optional[list] = Field(None, description="List of errors if any occurred")

    class Config:
        json_schema_extra = {
            "example": {
                "collection_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "started_at": "2026-01-09T10:30:00Z",
                "completed_at": "2026-01-09T10:52:00Z",
                "trends_found": 47,
                "duration_minutes": 22.5,
                "errors": None
            }
        }
