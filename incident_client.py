"""Client for Incident.io API."""

from datetime import datetime, timedelta
from typing import List, Optional
import httpx
from models import Incident, IncidentService, IncidentSeverity, IncidentStatus
from config import INCIDENT_IO_BASE_URL, DEFAULT_PAGE_SIZE, SERVICE_FIELD_ID


class IncidentIOClient:
    """Client for interacting with Incident.io API."""

    def __init__(self, api_token: str):
        """Initialize the client with API token.

        Args:
            api_token: The Incident.io API token

        Raises:
            ValueError: If api_token is empty or None
        """
        if not api_token:
            raise ValueError("API token is required")

        self.api_token = api_token
        self.base_url = INCIDENT_IO_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def get_incidents(
        self,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        page_size: int = DEFAULT_PAGE_SIZE
    ) -> List[Incident]:
        """
        Fetch incidents from the API (single page only).

        Args:
            status: Filter by incident status (e.g., 'closed', 'investigating')
            since: Start date for filtering incidents
            until: End date for filtering incidents
            page_size: Number of incidents to fetch (default 500, max 500)

        Note: When both since and until are provided, uses created_at[date_range].
              When only one is provided, uses created_at[gte] or created_at[lte].

        Returns:
            List of Incident objects (up to page_size incidents)
        """
        incidents = []

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/incidents"
            params = {"page_size": page_size}

            if status:
                params["status"] = status
            if since and until:
                # Use date_range operator for filtering between two dates (tilde-separated)
                params["created_at[date_range]"] = f"{since.strftime('%Y-%m-%d')}~{until.strftime('%Y-%m-%d')}"
            elif since:
                # Use gte operator for filtering from a start date
                params["created_at[gte]"] = since.strftime('%Y-%m-%d')
            elif until:
                # Use lte operator for filtering to an end date
                params["created_at[lte]"] = until.strftime('%Y-%m-%d')

            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()

                # Parse incidents
                for incident_data in data.get("incidents", []):
                    try:
                        incident = self._parse_incident(incident_data)
                        incidents.append(incident)
                    except Exception as e:
                        incident_id = incident_data.get('id', 'unknown')
                        print(f"⚠️  Warning: Failed to parse incident {incident_id}: {e}")
                        continue

            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP error fetching incidents: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Unexpected error fetching incidents: {e}")
                raise

        return incidents

    async def get_public_incidents_last_n_days(self, days: int) -> List[Incident]:
        """
        Fetch all public incidents from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of public Incident objects from the specified time period
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        print(f"🔍 Looking back {days} days for incidents (from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

        # Get incidents from the specified time period
        print("📥 Fetching incidents...")
        all_incidents = await self.get_incidents(since=start_date, until=end_date)

        print(f"📊 Retrieved {len(all_incidents)} total incidents")

        # Filter for public incidents only
        public_incidents = [
            incident for incident in all_incidents
            if incident.visibility == "public"
        ]

        print(f"📊 Found {len(public_incidents)} public incidents")
        return public_incidents

    def _parse_incident(self, incident_data: dict) -> Incident:
        """Parse incident data from API response into Incident model."""
        # Parse services - they are stored in custom_field_entries
        services = []

        # First check custom field entries for affected services
        custom_field_entries = incident_data.get("custom_field_entries", [])

        for entry in custom_field_entries:
            custom_field = entry.get("custom_field", {})
            # Look for the specific affected services custom field by ID
            custom_field_id = custom_field.get("id", "")

            if custom_field_id == SERVICE_FIELD_ID:
                values = entry.get("values", [])
                for value in values:
                    value_catalog_entry = value.get("value_catalog_entry", {})
                    if value_catalog_entry:
                        service_id = value_catalog_entry.get("external_id") or value_catalog_entry.get("id")
                        service_name = (value_catalog_entry.get("name") or
                                       value_catalog_entry.get("title") or
                                       service_id or "Unknown Service")

                        if service_id:
                            service = IncidentService(
                                id=service_id,
                                name=service_name,
                                summary=value_catalog_entry.get("summary", value_catalog_entry.get("description"))
                            )
                            services.append(service)

        # Parse severity - it might be nested or direct
        severity_data = incident_data.get("severity", {})
        if isinstance(severity_data, dict):
            severity = IncidentSeverity(
                id=severity_data.get("id", "unknown"),
                name=severity_data.get("name", "Unknown"),
                rank=severity_data.get("rank", 0)
            )
        else:
            # If severity is just an ID string
            severity = IncidentSeverity(
                id=str(severity_data) if severity_data else "unknown",
                name="Unknown",
                rank=0
            )

        # Parse status - check both 'status' and 'incident_status'
        status_data = incident_data.get("incident_status", incident_data.get("status", {}))
        if isinstance(status_data, dict):
            status = IncidentStatus(
                id=status_data.get("id", "unknown"),
                name=status_data.get("name", "Unknown"),
                category=status_data.get("category", "unknown")
            )
        else:
            # If status is just an ID string
            status = IncidentStatus(
                id=str(status_data) if status_data else "unknown",
                name="Unknown",
                category="unknown"
            )

        # Parse timestamps with better error handling
        try:
            created_at = datetime.fromisoformat(incident_data["created_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            created_at = datetime.now()

        try:
            updated_at = datetime.fromisoformat(incident_data["updated_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            updated_at = created_at

        resolved_at = None
        if incident_data.get("resolved_at"):
            try:
                resolved_at = datetime.fromisoformat(incident_data["resolved_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return Incident(
            id=incident_data.get("id", "unknown"),
            name=incident_data.get("name", "Unknown Incident"),
            summary=incident_data.get("summary"),
            description=incident_data.get("description"),
            created_at=created_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            severity=severity,
            status=status,
            services=services,
            visibility=incident_data.get("visibility", "private")
        )
