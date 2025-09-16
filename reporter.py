"""Report generator for correlating incidents with service scorecard data."""

from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

from models import (
    Incident,
    ServiceImpactReport,
    IncidentReport
)
from incident_client import IncidentIOClient
from cortex_client import CortexIOClient
from config import SCORECARD_DISPLAY_NAMES, MAX_SERVICES_DISPLAYED, MAX_FAILING_RULES_DISPLAYED


class IncidentServiceReporter:
    """Generates reports correlating incidents with service scorecard scores."""

    def __init__(self, incident_client: IncidentIOClient, cortex_client: CortexIOClient):
        """Initialize the reporter with API clients.

        Args:
            incident_client: Client for Incident.io API
            cortex_client: Client for Cortex.io API
        """
        self.incident_client = incident_client
        self.cortex_client = cortex_client

    async def generate_report(self, scorecard_tag: str = None, lookback_days: int = 30) -> IncidentReport:
        """
        Generate a comprehensive report of incidents and their impact on service scores.

        Args:
            scorecard_tag: Specific scorecard to analyze (if None, uses target scorecards)
            lookback_days: Number of days to look back

        Returns:
            IncidentReport containing all analysis
        """

        # Define report period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        incidents = await self.incident_client.get_public_incidents_last_n_days(lookback_days)

        # Extract unique service names from incidents
        impacted_service_names = set()
        for incident in incidents:
            for service in incident.services:
                impacted_service_names.add(service.name)

        # Group incidents by service
        service_incidents_map = self._group_incidents_by_service(incidents)

        # Fetch scorecard data for impacted services
        print("📈 Fetching scorecard data for impacted services...")
        service_scorecard_map = await self.cortex_client.get_target_scorecards_for_services(
            list(impacted_service_names)
        )

        # Generate service impact reports
        service_reports = []
        for service_name, incident_list in service_incidents_map.items():
            # Find matching scorecards (try both exact match and fuzzy match)
            matching_scorecards = []
            service_tag = None

            # First try exact matches by service name
            for tag, scorecards in service_scorecard_map.items():
                if tag.lower() == service_name.lower():
                    matching_scorecards = scorecards
                    service_tag = tag
                    break

            # If no exact match, try fuzzy matching
            if not matching_scorecards:
                for tag, scorecards in service_scorecard_map.items():
                    if (service_name.lower() in tag.lower() or
                        tag.lower() in service_name.lower()):
                        matching_scorecards = scorecards
                        service_tag = tag
                        break

            # Create service impact report
            service_report = ServiceImpactReport(
                service_name=service_name,
                service_tag=service_tag or service_name,
                incident_count=len(incident_list),
                incidents=[incident.id for incident in incident_list],
                scorecards=matching_scorecards,
                total_score=None  # We'll calculate this from all scorecards if needed
            )
            service_reports.append(service_report)

        # Sort by incident count (most impacted first)
        service_reports.sort(key=lambda x: x.incident_count, reverse=True)

        return IncidentReport(
            report_generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_incidents=len(incidents),
            impacted_services=service_reports
        )

    def _group_incidents_by_service(self, incidents: List[Incident]) -> Dict[str, List[Incident]]:
        """Group incidents by the services they impact."""
        service_incidents = defaultdict(list)

        for incident in incidents:
            for service in incident.services:
                service_incidents[service.name].append(incident)

        return dict(service_incidents)

    def print_report_summary(self, report: IncidentReport) -> None:
        """Print a human-readable summary of the report."""
        print("\n" + "="*80)
        print("🔥 INCIDENT & SERVICE SCORECARD REPORT")
        print("="*80)
        print(f"📅 Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}")
        print(f"📊 Total Public Incidents: {report.total_incidents}")
        print(f"🎯 Impacted Services: {len(report.impacted_services)}")
        print("\n" + "-"*80)
        print("📈 SERVICE IMPACT ANALYSIS")
        print("-"*80)

        for i, service_report in enumerate(report.impacted_services[:MAX_SERVICES_DISPLAYED], 1):
            print(f"{i:2d}. {service_report.service_name}")
            print(f"    🔥 {service_report.incident_count} incidents")

            # Display information for each scorecard
            if service_report.scorecards:
                for scorecard in service_report.scorecards:
                    scorecard_name = SCORECARD_DISPLAY_NAMES.get(
                        scorecard.scorecard_tag,
                        scorecard.scorecard_tag.replace("-", " ").title()
                    )

                    score_info = ""
                    level_info = ""

                    if scorecard.total_score is not None:
                        score_info = f"Score: {scorecard.total_score:.1f}"

                    if scorecard.current_level:
                        level_info = f"Level: {scorecard.current_level}"

                    info_parts = [part for part in [score_info, level_info] if part]
                    info_str = " | ".join(info_parts) if info_parts else "No score/level data"

                    print(f"    📊 {scorecard_name}: {info_str}")

                    # Show top failing rules for this scorecard
                    failing_scores = [
                        score for score in scorecard.scores
                        if score.score is not None and score.score < 1.0
                    ]

                    if failing_scores:
                        print(f"    📉 Failing {scorecard_name} rules:")
                        for score in failing_scores[:MAX_FAILING_RULES_DISPLAYED]:
                            score_val = score.score or 0
                            print(f"       • {score.rule.title}: {score_val:.1f}")
            else:
                print("    ❌ No scorecard data found")

            print()

        if len(report.impacted_services) > MAX_SERVICES_DISPLAYED:
            print(f"... and {len(report.impacted_services) - MAX_SERVICES_DISPLAYED} more services")

        print("\n" + "="*80)
