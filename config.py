"""Configuration constants and settings for the Incident.io & Cortex.io integration tool."""

import os
from typing import List

# API Configuration
INCIDENT_IO_BASE_URL = "https://api.incident.io/v2"
CORTEX_BASE_URL = "https://api.getcortexapp.com/api/v1"

# Default Configuration
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_PAGE_SIZE = 250

# Report Configuration
MAX_SERVICES_DISPLAYED = 15
MAX_FAILING_RULES_DISPLAYED = 5

# Environment Variable Names
ENV_INCIDENT_IO_TOKEN = "INCIDENT_IO_API_TOKEN"
ENV_CORTEX_TOKEN = "CORTEX_API_TOKEN"
ENV_TARGET_SCORECARD_TAGS = "TARGET_SCORECARD_TAGS"
ENV_SERVICE_FIELD_ID = "SERVICE_FIELD_ID"


def get_incident_io_token() -> str:
    """Get the Incident.io API token from environment variables."""
    token = os.getenv(ENV_INCIDENT_IO_TOKEN)
    if not token:
        raise ValueError(f"{ENV_INCIDENT_IO_TOKEN} environment variable is required")
    return token


def get_cortex_token() -> str:
    """Get the Cortex.io API token from environment variables."""
    token = os.getenv(ENV_CORTEX_TOKEN)
    if not token:
        raise ValueError(f"{ENV_CORTEX_TOKEN} environment variable is required")
    return token


def get_target_scorecard_tags() -> List[str]:
    """Get the target scorecard tag IDs from environment variables."""
    tags_str = os.getenv(ENV_TARGET_SCORECARD_TAGS)
    if not tags_str:
        raise ValueError(f"{ENV_TARGET_SCORECARD_TAGS} environment variable is required")

    # Split by comma and strip whitespace
    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    if not tags:
        raise ValueError(f"{ENV_TARGET_SCORECARD_TAGS} must contain at least one scorecard tag ID")

    return tags


def get_service_field_id() -> str:
    """Get the service custom field ID from environment variables."""
    field_id = os.getenv(ENV_SERVICE_FIELD_ID)
    if not field_id:
        raise ValueError(f"{ENV_SERVICE_FIELD_ID} environment variable is required")
    return field_id
