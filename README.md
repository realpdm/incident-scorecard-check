# Incident Service Incident Reporting Tool

A Python tool that fetches public incidents from a configurable lookback period (default: 30 days) from Incident.io and analyzes the scorecard scores of impacted services from Cortex.io.

This tool was made as simple demonstration of the using the [Incident.io](https://www.cortex.io/) and [Cortex](https://cortex.io) APIs together to produce something useful. Consider the code _alpha_ at best. 

## Features

- 🔍 Fetches public incidents from a configurable lookback period using Incident.io API
- 📊 Retrieves scorecard data for impacted services from Cortex.io API
- 📈 Correlates incidents with service scorecard performance
- 📋 Generates comprehensive reports showing service impact analysis
- 🎯 Type-safe implementation using Pydantic models and Python type hints

## Requirements

- Python 3.13+
- UV package manager
- API tokens for both Incident.io and Cortex.io

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure API tokens:**
   ```bash
   cp .env.example .env
   # Edit .env and add your actual API tokens
   ```

3. **Get API tokens:**
   - **Incident.io**: https://app.incident.io/settings/api-keys
   - **Cortex.io**: https://app.getcortexapp.com/admin/settings/api-keys

## Configuration

The tool uses command line arguments for configuration:

- `--days N`: Number of days to look back for incidents (default: 30)

## Usage

Run the tool to generate a report:

```bash
# Basic usage with default 30-day lookback
uv run main.py

# Custom lookback period
uv run main.py --days 7

# Combine options
uv run main.py --days 14
```

### Command Line Options

- `--days N`: Number of days to look back for incidents (default: 30)
- `--help, -h`: Show help message

The tool will:
1. Fetch all public incidents from the configured lookback period (default: last 30 days)
2. Extract the services impacted by these incidents
3. Retrieve scorecard data for those services from Cortex.io (filtered to "Operational Readiness" and "Security" scorecards)
4. Generate a comprehensive report showing:
   - Total number of incidents
   - Services ranked by incident frequency
   - Scorecard scores for impacted services
   - Failing scorecard rules for each service

## Project Structure

```
├── main.py              # Main entry point with CLI
├── config.py            # Configuration constants and settings
├── models.py            # Pydantic data models for both APIs
├── incident_client.py   # Incident.io API client
├── cortex_client.py     # Cortex.io API client
├── reporter.py          # Report generation logic
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
└── pyproject.toml       # Project dependencies and metadata
```

## API Models

The tool uses strongly-typed Pydantic models for:

- **Incident.io**: `Incident`, `IncidentService`, `IncidentSeverity`, `IncidentStatus`
- **Cortex.io**: `ServiceScorecard`, `ScorecardScore`, `ScorecardRule`, `CortexService`
- **Reports**: `ServiceImpactReport`, `IncidentReport`

## Error Handling

The tool includes error handling for:
- Missing API tokens
- Network connectivity issues
- API rate limits and authentication errors
- Service matching between different APIs

## Example Output

```
🔥 INCIDENT & SERVICE SCORECARD REPORT
================================================================================
📅 Period: 2025-08-16 to 2025-09-15
📊 Total Public Incidents: 15
🎯 Impacted Services: 8

--------------------------------------------------------------------------------
📈 SERVICE IMPACT ANALYSIS
--------------------------------------------------------------------------------
 1. payment-service
   🔥 2 incidents
    📊 Operational Readiness: Score: 9.0 | Level: Gold
    📊 Security: Score: 2.0 | Level: Silver
    📉 Failing Security rules:
       • Has no Cycode SAST/SCA high detections: 0.0

 2. user-authentication
    🔥 1 incidents
    📊 Operational Readiness: Score: 9.0 | Level: Gold
    📊 Security: Score: 3.0 | Level: Gold
```
