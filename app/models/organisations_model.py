"""
This module contains the SQLModel-based models related to `Organisation`, 
including the database table definition and the Pydantic model for creating an organisation.
"""
from typing import Optional, List
from sqlmodel import Field, Relationship
from .base import Base

class Organisation(Base, table=True):
    """
    Database model representing an `Organisation`.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    locations: List["Location"] = Relationship(back_populates="organisation")

class CreateOrganisation(Base):
    """
    Pydantic model for creating an `Organisation`.
    """
    name: str
