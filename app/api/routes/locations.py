"""
This module defines the API endpoints for managing organisation locations.
"""
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_
from app.db import get_db
from app.models import Location, LocationCreate, Organisation
from app.logger import logger

router = APIRouter()

@router.post("/create/location", response_model=Location)
def create_location(*, session: Session = Depends(get_db), location: LocationCreate):
    """
    Create a new location for a given organisation.
    Returns: Location: The created location.
    """
    try:
        organisation = session.get(Organisation, location.organisation_id)
        if not organisation:
            raise HTTPException(status_code=404, detail="Organisation not found")

        new_location = Location(
            organisation_id=location.organisation_id,
            location_name=location.location_name,
            longitude=location.longitude,
            latitude=location.latitude,
        )
        session.add(new_location)
        session.commit()
        session.refresh(new_location)
        return new_location
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        session.rollback()
        logger.error("Error creating location: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/{organisation_id}/locations", response_model=List[Location])
def get_organisation_locations(
    organisation_id: int,
    session: Session = Depends(get_db),
    bounding_box: Optional[Tuple[float, float, float, float]] = 
        Query(None, description="Tuple of 4 bounding coordinates (min_longitude, min_latitude, max_longitude, max_latitude)")
    ):
    """
    Retrieve all locations for a specific organisation.
    Returns: List[Location]: A list of locations for the specified organisation.
    """
    try:
        if bounding_box:
            min_longitude, min_latitude, max_longitude, max_latitude = bounding_box
            if min_longitude >= max_longitude or min_latitude >= max_latitude:
                raise HTTPException(status_code=400, detail="Invalid bounding box coordinates.")

            query = select(Location).where(
                and_(
                    Location.organisation_id == organisation_id,
                    Location.longitude >= min_longitude,
                    Location.longitude <= max_longitude,
                    Location.latitude >= min_latitude,
                    Location.latitude <= max_latitude
                )
            )
        else:
            query = select(Location).where(Location.organisation_id == organisation_id)
            
        locations = session.exec(query).all()

        if not locations:
            raise HTTPException(status_code=404, detail=f"No locations found for Organisation - {organisation_id}")
        return locations
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Error retrieving organisation locations: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
    