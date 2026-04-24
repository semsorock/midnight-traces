# Midnight Traces

Visualizing token transactions with Sankey diagrams.

![Example Styled Sankey Diagram](assets/example_sankey.png)

## Key Features
- **Data Ingestion**: Fetch token transactions from SQL databases.
- **Visualisation**: Generate Sankey diagrams using Plotly.
- **Styling**: Apply custom styles using Google Gemini API.
- **Social Sharing**: Post updates to Twitter.

## Getting Started

### Prerequisites
- Python 3.10+
- [Poetry](https://python-poetry.org/) (Dependency Management)

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   make install
   ```
3. Set up environment variables:
   Copy the example config and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   You will need a PostgreSQL DB connection string, a Google Gemini API Key, and Twitter API credentials.

### Verifying Setup

Before running the full pipeline, check that your `.env` is configured correctly:
```bash
poetry run python pipeline.py --check-ready
```

### Running the Pipeline

To run the main pipeline for yesterday's data (without posting to Twitter):
```bash
make run
```

To run for a specific date and post the results to Twitter:
```bash
make run ARGS="--post-twitter --date 2025-12-22"
```

Other helpful arguments:
- `--skip-styling`: Generate the raw Sankey diagram without the Gemini styling step.
- `--max-tx-count 50`: Limit the visualization to the top 50 transactions.

### Development

- **Testing**: Run `make test` to execute the test suite via `pytest`.
- **Cleaning**: Run `make clean` to remove cache files.
