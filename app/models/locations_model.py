"""
This module contains the SQLModel-based models related to `Location`, 
including the database table definition and the Pydantic model for creating a location.
"""

from typing import Optional
from sqlmodel import Field, Relationship
from .base import Base
from .organisations_model import Organisation

class Location(Base, table=True):
    """
    Database model representing a Location.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    organisation_id: int = Field(foreign_key="organisation.id")
    organisation: Organisation = Relationship(back_populates="locations")
    location_name: str
    longitude: float
    latitude: float

class LocationCreate(Base):
    """
    Pydantic model for creating a Location.
    """
    organisation_id: int
    location_name: str
    longitude: float
    latitude: float
