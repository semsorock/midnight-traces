# Midnight Traces

Visualizing token transactions with Sankey diagrams.

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

### Running the Pipeline

To run the main pipeline:
```bash
make run ARGS="--post-twitter --date 2025-12-22"
```

### Development

- **Linting**: (Add lint command if applicable)
- **Testing**: `make test`
