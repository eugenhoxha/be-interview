"""
Base class for all models
"""

from sqlmodel import SQLModel

class Base(SQLModel):
    """
    Base class to be inherited by all models.
    Can include common metadata or shared properties in the future.
    """
    pass