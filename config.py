"""Configuration constants and settings for the Incident.io & Cortex.io integration tool."""

import os
from typing import Dict, List

# API Configuration
INCIDENT_IO_BASE_URL = "https://api.incident.io/v2"
CORTEX_BASE_URL = "https://api.getcortexapp.com/api/v1"

# Default Configuration
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_PAGE_SIZE = 250

# Target Scorecards Configuration
# These are the scorecards we want to analyze for service health
TARGET_SCORECARDS: Dict[str, str] = {
    "1234": "Operational Readiness",
    "3456": "Security"
}

# Scorecard name mappings for display
SCORECARD_DISPLAY_NAMES: Dict[str, str] = {
    "operational-readiness": "Operational Readiness",
    "security": "Security"
}

# Service custom field ID for incident parsing
SERVICE_FIELD_ID: str = "XXXXXXXXXXX1111111111"

# Report Configuration
MAX_SERVICES_DISPLAYED = 15
MAX_FAILING_RULES_DISPLAYED = 5

# Environment Variable Names
ENV_INCIDENT_IO_TOKEN = "INCIDENT_IO_API_TOKEN"
ENV_CORTEX_TOKEN = "CORTEX_API_TOKEN"


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
