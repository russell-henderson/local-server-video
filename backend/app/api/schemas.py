"""
backend/app/api/schemas.py

Pydantic models for request/response validation.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RatingInput(BaseModel):
    """Request body for setting a rating."""

    value: int = Field(
        ...,
        ge=1,
        le=5,
        description="User rating value (1-5)"
    )

    @field_validator('value')
    @classmethod
    def validate_value_range(cls, v: int) -> int:
        """Ensure value is within valid range."""
        if not isinstance(v, int):
            raise ValueError('Rating value must be an integer')
        if v < 1 or v > 5:
            raise ValueError('Rating value must be between 1 and 5')
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {"value": 4}
        }


class RatingUser(BaseModel):
    """User's rating for a video."""

    value: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="User's rating value"
    )


class RatingSummary(BaseModel):
    """Summary of ratings for a video."""

    average: float = Field(
        ...,
        ge=0,
        le=5,
        description="Average rating (0-5)"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of ratings"
    )
    user: RatingUser = Field(
        ...,
        description="Current user's rating"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "average": 4.5,
                "count": 2,
                "user": {"value": 5}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        None,
        description="Additional error details"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "Rating must be between 1 and 5",
                "detail": None
            }
        }
