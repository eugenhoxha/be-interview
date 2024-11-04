from pathlib import Path
from typing import Generator
from unittest.mock import patch
from uuid import uuid4
from fastapi import status
import alembic.command
import alembic.config
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db import get_database_session
from app.main import app
from app.models import Organisation, Location

_ALEMBIC_INI_PATH = Path(__file__).parent.parent / "alembic.ini"

@pytest.fixture()
def test_client() -> TestClient:
    """
    Creates a TestClient for the FastAPI app.
    """
    return TestClient(app)

@pytest.fixture(autouse=True)
def apply_alembic_migrations() -> Generator[None, None, None]:
    """
    Applies alembic migrations to a temporary SQLite database for each test.
    """
    test_db_file_name = f"test_{uuid4()}.db"
    database_path = Path(test_db_file_name)
    try:
        test_db_url = f"sqlite:///{test_db_file_name}"
        alembic_cfg = alembic.config.Config(_ALEMBIC_INI_PATH)
        alembic_cfg.attributes["sqlalchemy_url"] = test_db_url
        alembic.command.upgrade(alembic_cfg, "head")
        test_engine = create_engine(test_db_url, echo=True)
        with patch("app.db.get_engine") as mock_engine:
            mock_engine.return_value = test_engine
            yield
    finally:
        database_path.unlink(missing_ok=True)

def test_organisation_endpoints(test_client: TestClient) -> None:
    """
    Test creating organisations and locations, ensuring they are correctly inserted into the database,
    retrieving them via the API, and testing retrieval locations with bounding boxes.
    """
    list_of_organisation_names_to_create = ["organisation_a", "organisation_b", "organisation_c"]
    list_of_location_data_to_create = [
        {"organisation_id": 1, "location_name": "first_location", "longitude": 48.210, "latitude": 16.363},
        {"organisation_id": 1, "location_name": "second_location", "longitude": 49.330, "latitude": 17.0},
        {"organisation_id": 1, "location_name": "third_location", "longitude": 45.0, "latitude": 20.5},
    ]
    
    # Validate that organisations do not exist in database
    with get_database_session() as database_session:
        organisations_before = database_session.query(Organisation).all()
        database_session.expunge_all()
    assert len(organisations_before) == 0

    # Create organisations
    for organisation_name in list_of_organisation_names_to_create:
        response = test_client.post("/api/organisations/create", json={"name": organisation_name})
        assert response.status_code == status.HTTP_200_OK

    # Validate that organisations exist in the database
    with get_database_session() as database_session:
        organisations_after = database_session.query(Organisation).all()
        database_session.expunge_all()
    created_organisation_names = {org.name for org in organisations_after}
    assert created_organisation_names == set(list_of_organisation_names_to_create), (
        f"Expected organisations {set(list_of_organisation_names_to_create)}, found {created_organisation_names}"
    )

    # Use the first created organisation for location tests
    org_id = organisations_after[0].id

    # Validate that the given locations do not exist for this organisation
    expected_location_names = {loc["location_name"] for loc in list_of_location_data_to_create}

    with get_database_session() as database_session:
        existing_locations = database_session.query(Location).filter_by(organisation_id=org_id).all()
        existing_location_names = {loc.location_name for loc in existing_locations}
        database_session.expunge_all()
    
    # Ensure that none of the expected locations are already in the database
    assert existing_location_names.isdisjoint(expected_location_names), (
        f"Some locations already exist for organisation ID {org_id}: "
        f"{existing_location_names.intersection(expected_location_names)}"
    )

    # Create locations via API
    for loc in list_of_location_data_to_create:
        response = test_client.post("/api/organisations/create/location", json={
            "organisation_id": loc["organisation_id"],
            "location_name": loc["location_name"],
            "longitude": loc["longitude"],
            "latitude": loc["latitude"]
        })
        assert response.status_code == status.HTTP_200_OK, f"Failed to create location '{loc['location_name']}'."

    # Retrieve locations and validate
    response = test_client.get(f"/api/organisations/{org_id}/locations")
    assert response.status_code == status.HTTP_200_OK, f"Failed to retrieve locations for organisation ID {org_id}."
    data = response.json()
    retrieved_location_names = {loc["location_name"] for loc in data}
    expected_location_names = {loc["location_name"] for loc in list_of_location_data_to_create}
    assert retrieved_location_names == expected_location_names, (
        f"Expected locations {expected_location_names}, got {retrieved_location_names}."
    )
    
    # Retrieve locations using bounding boxes and validate
    bounding_box_tests = [
        {
            "bounding_box": "45.0,15.0,50.0,22.0",
            "expected_status": status.HTTP_200_OK,
            "expected_locations": {"first_location", "second_location", "third_location"}
        },
        {
            "bounding_box": "47.0,16.0,49.0,18.0",
            "expected_status": status.HTTP_200_OK,
            "expected_locations": {"first_location"}
        },
        {
            "bounding_box": "40.0,10.0,44.0,14.0",
            "expected_status": status.HTTP_404_NOT_FOUND,
            "expected_locations": set()
        },
        {
            "bounding_box": "50.0,20.0,49.0,19.0",  # Invalid coordinates (min >= max)
            "expected_status": status.HTTP_400_BAD_REQUEST,
            "expected_locations": None
        },
        {
            "bounding_box": "45.0,15.0",  # Insufficient coordinates
            "expected_status": status.HTTP_400_BAD_REQUEST,
            "expected_locations": None
        }
    ]
        
    for test_case in bounding_box_tests:
        bounding_box = test_case["bounding_box"].split(",")
        expected_status = test_case["expected_status"]
        expected_locations = test_case["expected_locations"]
        if len(bounding_box) == 4:  # Ensure only valid tests are run with four coordinates
            response = test_client.get(
                f"/api/organisations/{org_id}/locations",
                params={
                    "bounding_box": [bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]]
                }
            )
            assert response.status_code == expected_status, (
                f"For bounding box {bounding_box}, expected status {expected_status}, got {response.status_code}."
            )

            if expected_status == status.HTTP_200_OK:
                data = response.json()
                retrieved_location_names = {loc["location_name"] for loc in data}
                assert retrieved_location_names == expected_locations, (
                    f"For bounding box {bounding_box}, expected locations {expected_locations}, got {retrieved_location_names}."
                )
            elif expected_status in {status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND}:
                assert "detail" in response.json(), f"Expected error detail for bounding box {bounding_box}."
        else:
            response = test_client.get(
                f"/api/organisations/{org_id}/locations",
                params={"bounding_box": bounding_box}
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"For insufficient bounding box coordinates {bounding_box}, expected status {status.HTTP_422_UNPROCESSABLE_ENTITY}."
            )