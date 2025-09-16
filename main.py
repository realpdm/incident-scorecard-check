"""
Incident.io and Cortex.io Integration Tool

This tool fetches public incidents from a configurable lookback period and analyzes
the scorecard scores of impacted services from Cortex.io.
"""

import argparse
import asyncio
import sys
from dotenv import load_dotenv

from config import get_incident_io_token, get_cortex_token, DEFAULT_LOOKBACK_DAYS
from incident_client import IncidentIOClient
from cortex_client import CortexIOClient
from reporter import IncidentServiceReporter


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze incidents and their impact on service scorecard scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use default 30-day lookback
  %(prog)s --days 7           # Look back 7 days
  %(prog)s --days 14          # Look back 14 days
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to look back for incidents (default: 30)",
    )

    return parser.parse_args()


async def main() -> None:
    """Main entry point for the incident service scorecard analysis tool."""
    # Parse command line arguments
    args = parse_arguments()

    # Load environment variables
    load_dotenv()

    print("🚀 Starting Incident & Service Scorecard Analysis Tool")
    print("=" * 60)

    try:
        # Get configuration
        lookback_days = args.days or DEFAULT_LOOKBACK_DAYS

        # Initialize API clients
        print("🔧 Initializing API clients...")

        incident_token = get_incident_io_token()
        cortex_token = get_cortex_token()

        incident_client = IncidentIOClient(incident_token)
        cortex_client = CortexIOClient(cortex_token)

        # Create reporter
        reporter = IncidentServiceReporter(incident_client, cortex_client)

        # Generate the report
        print(
            f"📊 Generating incident and service scorecard report for last {lookback_days} days..."
        )

        report = await reporter.generate_report(lookback_days=lookback_days)

        # Display the report
        reporter.print_report_summary(report)

        print("✅ Report generation completed successfully!")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
