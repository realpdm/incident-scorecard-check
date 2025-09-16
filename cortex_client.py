"""Client for Cortex.io API."""

from typing import List, Optional, Dict, Any
import httpx
from models import ServiceScorecard, ScorecardScore, ScorecardRule, CortexService
from config import CORTEX_BASE_URL, TARGET_SCORECARDS


class CortexIOClient:
    """Client for interacting with Cortex.io API."""

    def __init__(self, api_token: str):
        """Initialize the client with API token.

        Args:
            api_token: The Cortex.io API token

        Raises:
            ValueError: If api_token is empty or None
        """
        if not api_token:
            raise ValueError("API token is required")

        self.api_token = api_token
        self.base_url = CORTEX_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def get_services(self) -> List[CortexService]:
        """
        Fetch all services from Cortex.io by getting them from scorecard data.

        Returns:
            List of CortexService objects
        """
        services = []
        seen_services = set()

        async with httpx.AsyncClient() as client:
            try:
                scorecards_response = await client.get(
                    f"{self.base_url}/scorecards",
                    headers=self.headers
                )
                scorecards_response.raise_for_status()
                scorecards_data = scorecards_response.json()

                scorecards = scorecards_data.get("scorecards", [])
                if not scorecards:
                    return services

                scorecard_tag = scorecards[0]["tag"]

                scores_response = await client.get(
                    f"{self.base_url}/scorecards/{scorecard_tag}/scores",
                    headers=self.headers,
                    params={"pageSize": 1000}
                )
                scores_response.raise_for_status()
                scores_data = scores_response.json()

                for service_score in scores_data.get("serviceScores", []):
                    service_data = service_score.get("service", {})
                    service_tag = service_data.get("tag")

                    if service_tag and service_tag not in seen_services:
                        service = CortexService(
                            tag=service_tag,
                            title=service_data.get("name", service_tag),
                            summary=service_data.get("description"),
                            type="service"
                        )
                        services.append(service)
                        seen_services.add(service_tag)

            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP error fetching services from Cortex: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Unexpected error fetching services from Cortex: {e}")
                raise

        return services

    async def get_service_scorecard(
        self,
        service_tag: str,
        scorecard_tag: str
    ) -> Optional[ServiceScorecard]:
        """
        Fetch scorecard data for a specific service.

        Args:
            service_tag: The service identifier
            scorecard_tag: The scorecard identifier

        Returns:
            ServiceScorecard object or None if not found
        """
        async with httpx.AsyncClient() as client:
            try:
                # First get the scorecard definition to get rule titles
                scorecard_def_response = await client.get(
                    f"{self.base_url}/scorecards/{scorecard_tag}",
                    headers=self.headers
                )
                scorecard_def_response.raise_for_status()
                scorecard_def = scorecard_def_response.json().get("scorecard", {})

                rule_info_map = {}
                for rule in scorecard_def.get("rules", []):
                    rule_info_map[rule.get("identifier")] = {
                        "title": rule.get("title", rule.get("identifier", "")),
                        "description": rule.get("description", ""),
                        "weight": rule.get("weight")
                    }

                response = await client.get(
                    f"{self.base_url}/scorecards/{scorecard_tag}/scores",
                    headers=self.headers,
                    params={"entityTag": service_tag}
                )
                response.raise_for_status()

                data = response.json()

                for service_score in data.get("serviceScores", []):
                    service_data = service_score.get("service", {})
                    if service_data.get("tag") == service_tag:
                        return self._parse_scorecard_from_service_score(
                            service_tag, scorecard_tag, service_score, rule_info_map
                        )

                return None

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise

    async def get_scorecards(self) -> List[Dict[str, Any]]:
        """
        Fetch all available scorecards.

        Returns:
            List of scorecard metadata
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/scorecards",
                headers=self.headers
            )
            response.raise_for_status()

            return response.json().get("scorecards", [])

    async def get_service_scorecards_by_names(
        self,
        service_names: List[str],
        scorecard_tags: Optional[List[str]] = None
    ) -> List[ServiceScorecard]:
        """
        Fetch scorecard data for multiple services by name.

        Args:
            service_names: List of service names to fetch scorecards for
            scorecard_tags: Specific scorecards to fetch (if None, uses filtered scorecards)

        Returns:
            List of ServiceScorecard objects
        """
        # Use the configured target scorecards
        target_scorecards = TARGET_SCORECARDS

        all_services = await self.get_services()
        service_tag_map = {
            service.title.lower(): service.tag
            for service in all_services
        }

        for service in all_services:
            service_tag_map[service.tag.lower()] = service.tag

        if not scorecard_tags:
            all_scorecards = await self.get_scorecards()
            scorecard_tags = []

            for scorecard in all_scorecards:
                scorecard_tag = scorecard.get("tag", "")
                scorecard_name = scorecard.get("name", "")

                for target_id, target_name in target_scorecards.items():
                    if (target_id in scorecard_tag or
                        target_name.lower() in scorecard_name.lower()):
                        scorecard_tags.append(scorecard_tag)
                        break

            if not scorecard_tags:
                return []

        # Fetch scorecards for matching services across all target scorecards
        service_scorecards = []

        for service_name in service_names:
            service_name_lower = service_name.lower()

            # Try to find matching service tag
            service_tag = None
            for name_key, tag in service_tag_map.items():
                if service_name_lower in name_key or name_key in service_name_lower:
                    service_tag = tag
                    break

            if service_tag:
                # Get scorecards for this service from all target scorecards
                for scorecard_tag in scorecard_tags:
                    scorecard = await self.get_service_scorecard(service_tag, scorecard_tag)
                    if scorecard:
                        service_scorecards.append(scorecard)

        return service_scorecards

    async def get_target_scorecards_for_services(
        self,
        service_names: List[str]
    ) -> Dict[str, List[ServiceScorecard]]:
        """
        Get scorecards for services grouped by service name.

        Args:
            service_names: List of service names to fetch scorecards for

        Returns:
            Dictionary mapping service names to their scorecards
        """
        all_scorecards = await self.get_service_scorecards_by_names(service_names)

        # Group scorecards by service
        service_scorecard_map = {}
        for scorecard in all_scorecards:
            service_tag = scorecard.service_tag
            if service_tag not in service_scorecard_map:
                service_scorecard_map[service_tag] = []
            service_scorecard_map[service_tag].append(scorecard)

        return service_scorecard_map

    def _parse_scorecard(
        self,
        service_tag: str,
        scorecard_tag: str,
        data: Dict[str, Any]
    ) -> ServiceScorecard:
        """Parse scorecard data from API response."""
        scores = []

        for score_data in data.get("scores", []):
            rule_data = score_data.get("rule", {})

            rule = ScorecardRule(
                expression=rule_data.get("expression", ""),
                level=rule_data.get("level", ""),
                title=rule_data.get("title", ""),
                description=rule_data.get("description"),
                weight=rule_data.get("weight")
            )

            score = ScorecardScore(
                rule=rule,
                score=score_data.get("score"),
                level=score_data.get("level")
            )
            scores.append(score)

        return ServiceScorecard(
            service_tag=service_tag,
            scorecard_tag=scorecard_tag,
            scores=scores,
            total_score=data.get("totalScore")
        )

    def _parse_scorecard_from_service_score(
        self,
        service_tag: str,
        scorecard_tag: str,
        service_score_data: Dict[str, Any],
        rule_info_map: Dict[str, Dict[str, Any]] = None
    ) -> ServiceScorecard:
        """Parse scorecard data from service score response."""
        scores = []
        score_data = service_score_data.get("score", {})
        rule_info_map = rule_info_map or {}

        # Parse individual rule scores
        for rule_score in score_data.get("rules", []):
            rule_identifier = rule_score.get("identifier", "")
            rule_info = rule_info_map.get(rule_identifier, {})

            rule = ScorecardRule(
                expression=rule_score.get("expression", ""),
                level="",  # Not provided in this format
                title=rule_info.get("title", rule_identifier),  # Use proper title from scorecard def
                description=rule_info.get("description", ""),
                weight=rule_info.get("weight")
            )

            score = ScorecardScore(
                rule=rule,
                score=rule_score.get("score"),
                level=None
            )
            scores.append(score)

        # Get total score and ladder levels from summary
        summary = score_data.get("summary", {})
        total_score = summary.get("score")

        # Extract ladder levels for the service
        ladder_levels = score_data.get("ladderLevels", [])
        current_level = None
        if ladder_levels:
            # Get the highest achieved level
            for level_info in ladder_levels:
                level = level_info.get("level", {})
                if level:
                    current_level = level.get("name", "")
                    break

        # Create an enhanced scorecard with level information
        scorecard = ServiceScorecard(
            service_tag=service_tag,
            scorecard_tag=scorecard_tag,
            scores=scores,
            total_score=total_score,
            current_level=current_level
        )

        return scorecard
