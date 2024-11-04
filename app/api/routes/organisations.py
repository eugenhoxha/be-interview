"""
This module defines the API endpoints for managing organisations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_db
from app.models import Organisation, CreateOrganisation
from app.logger import logger

router = APIRouter()

@router.get("/", response_model=list[Organisation])
def get_organisations(session: Session = Depends(get_db)) -> list[Organisation]:
    """
    Get all organisations.
    Returns: List[Organisation]: A list of all organisations.
    """
    try:
        organisations = session.exec(select(Organisation)).all()
        return organisations
    except Exception as e:
        logger.error("Error retrieving organisations: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/create", response_model=Organisation)
def create_organisation(org: CreateOrganisation, session: Session = Depends(get_db)) -> Organisation:
    """
    Create a new organisation.
    Returns: Organisation: The created organisation.
    """
    try:
        new_org = Organisation(name=org.name)
        session.add(new_org)
        session.commit()
        session.refresh(new_org)
        return new_org
    except Exception as e:
        session.rollback()
        logger.error("Error creating organisation: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{organisation_id}", response_model=Organisation)
def get_organisation(organisation_id: int, session: Session = Depends(get_db)) -> Organisation:
    """
    Get an organisation by id.
    Returns: Organisation: The organisation with the specified ID.
    """
    try:
        organisation = session.get(Organisation, organisation_id)
        if not organisation:
            raise HTTPException(status_code=404, detail="Organisation not found")
        return organisation
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Error retrieving organisation by ID: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
    