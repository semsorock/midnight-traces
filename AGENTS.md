# Midnight Traces - AI Agent Guidelines

This document provides context, architecture details, and operational guidelines for AI agents working on the `midnight_traces` codebase.

## 🎯 Project Overview
Midnight Traces is an automated pipeline that queries token transaction data from a Cardano DB-Sync database (specifically for the `$NIGHT` token), visualizes the flow of these tokens using Sankey diagrams via Plotly, applies stylistic enhancements using the Google Gemini API, and automatically posts the results to Twitter (X).

## 🏗️ Architecture & Pipeline
The core logic resides in a 3-stage pipeline orchestrated by `pipeline.py`:

1. **Data Ingestion & Visualization (`token_flow_sankey.py`)**:
   - Connects to a PostgreSQL database (Cardano DB-Sync).
   - Queries transaction data using SQL scripts (`token_transactions.sql`, `daily_token_stats.sql`).
   - Replaces the hardcoded date (`2025-12-06`) dynamically.
   - Limits visualization to the top transactions by volume (`max_tx_count`) to maintain Sankey legibility.
   - Generates a base Sankey diagram image using `plotly`.
2. **Styling (`style_sankey_gemini.py`)**:
   - Takes the raw Sankey diagram.
   - Uses the Gemini API (`gemini-2.5-pro` model) to interpret the image and apply a beautiful, thematic restyling.
   - Saves the final image to the `out/` directory.
3. **Social Sharing (`twitter.py`)**:
   - Uses `tweepy` to interface with the Twitter API v1.1 (for media upload) and v2 (for posting).
   - Generates formatted tweet copy including volume, transaction count, unique addresses, and flow count.

## ⚙️ Environment Setup
- **Language**: Python 3.10+
- **Dependency Management**: Poetry (`poetry.lock`, `pyproject.toml`)
- **Environment Variables**: Managed via `.env` (see `.env.example`).
  - `GOOGLE_API_KEY`: Required for Gemini image styling.
  - `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`: Required for Twitter posting.
  - `DB_CONNECTION_STRING`: Used by `token_flow_sankey.py`.

## 🛠️ Common Commands (via Makefile)
- **Install dependencies**: `make install`
- **Run pipeline (default: yesterday's data)**: `make run`
- **Run pipeline with arguments**: `make run ARGS="--post-twitter --date 2025-12-22"`
- **Test pipeline readiness**: `poetry run python pipeline.py --check-ready`
- **Clean cache**: `make clean`
- **Run tests**: `make test`

## 🧠 Guidelines for Agents
1. **SQL Modifications**: The `.sql` files target the `asset1wd3llgkhsw6etxf2yca6cgk9ssrpva3wf0pq9a` fingerprint ($NIGHT token). When modifying SQL, ensure compatibility with the standard Cardano DB-Sync schema (e.g., `tx`, `tx_out`, `ma_tx_out`). Avoid making queries too expensive; utilize `LIMIT` clauses where appropriate.
2. **Date Handling**: The pipeline defaults to UTC time and handles dates in `YYYY-MM-DD` format. Make sure date substitutions (done with regex in `token_flow_sankey.py`) won't break if you update the SQL format.
3. **Number Formatting**: Ensure large token volumes are formatted with human-readable suffixes (K, M, B, T, Q) via `format_token_amount` in `twitter.py` and `format_quantity` in `token_flow_sankey.py`. Note that token amounts are raw integers in DB with `TOKEN_DECIMALS = 6` (e.g. `1,000,000` = 1 `$NIGHT`).
4. **Resilience**: Wrap external API calls (Gemini, Twitter) in `try-except` blocks. If Gemini styling fails, the pipeline should gracefully fall back to the raw Sankey diagram.
5. **No Blind Executions**: Do not run the pipeline using `make run` or `pipeline.py` with `--post-twitter` unless you are absolutely sure, as this will post to the live account. Check the readiness first with `poetry run python pipeline.py --check-ready`.
