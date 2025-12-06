#!/usr/bin/env python3
"""
Token Flow Sankey Diagram Generator

Generates a vertical Sankey diagram showing token movement between addresses
based on transaction data from PostgreSQL database.

Usage:
    python token_flow_sankey.py                    # Uses yesterday's date (UTC)
    python token_flow_sankey.py --date 2025-12-05  # Uses specified date
"""

import argparse
import json
import os
import re
import psycopg2
import plotly.graph_objects as go
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Database connection string
DB_CONNECTION_STRING = "postgresql://dbsync10jarkq839ywtvh742nc:UbZEUkHLxSQ@cardano-mainnet.dbsync-v3.demeter.run:5432/dbsync-mainnet"


def load_transactions_from_db(sql_file: str, target_date: str) -> list:
    """
    Load and parse the token transactions from PostgreSQL database.
    
    Args:
        sql_file: Path to the SQL query file
        target_date: Date string in YYYY-MM-DD format (UTC)
    """
    # Read the SQL query from file
    with open(sql_file, 'r') as f:
        sql_query = f.read()
    
    # Replace the hardcoded date in the SQL with the target date
    # Matches pattern like: SELECT '2025-12-06'::date AS filter_date
    sql_query = re.sub(
        r"SELECT\s+'\d{4}-\d{2}-\d{2}'::date\s+AS\s+filter_date",
        f"SELECT '{target_date}'::date AS filter_date",
        sql_query
    )
    
    # Connect to the database and execute query
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Fetch column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows and convert to list of dicts
        transactions = []
        for row in cursor.fetchall():
            tx = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert JSONB fields to JSON strings for compatibility with existing parse_utxos function
                if col in ('input_utxos', 'output_utxos'):
                    tx[col] = json.dumps(value) if value else '[]'
                else:
                    tx[col] = value
            transactions.append(tx)
        
        return transactions
    finally:
        conn.close()


def shorten_address(address: str) -> str:
    """Shorten an address for display to minimal format like 'a..xyz'."""
    if len(address) <= 6:
        return address
    return f"{address[0]}..{address[-3:]}"


def parse_utxos(utxo_str: str) -> list:
    """Parse the UTXO JSON string into a list of dictionaries."""
    if not utxo_str or utxo_str == "[]":
        return []
    try:
        return json.loads(utxo_str)
    except json.JSONDecodeError:
        return []


def extract_flows(transactions: list) -> list:
    """
    Extract token flows from transactions.
    Returns a list of (source_address, target_address, quantity, tx_hash) tuples.
    """
    flows = []
    
    for tx in transactions:
        tx_hash = tx.get('tx_hash', 'Unknown')
        input_utxos = parse_utxos(tx.get('input_utxos', '[]'))
        output_utxos = parse_utxos(tx.get('output_utxos', '[]'))
        
        # Skip if no inputs (genesis/minting) or no outputs
        if not input_utxos or not output_utxos:
            continue
        
        # Calculate total input and output quantities
        total_input = sum(u.get('quantity', 0) for u in input_utxos)
        total_output = sum(u.get('quantity', 0) for u in output_utxos)
        
        # For each input address, distribute tokens proportionally to outputs
        for inp in input_utxos:
            source_addr = inp.get('address', 'Unknown')
            inp_quantity = inp.get('quantity', 0)
            
            if inp_quantity == 0 or total_output == 0:
                continue
            
            # Distribute to each output proportionally
            for out in output_utxos:
                target_addr = out.get('address', 'Unknown')
                out_quantity = out.get('quantity', 0)
                
                # Calculate the flow from this input to this output
                # Proportional to output's share of total output
                flow_quantity = (inp_quantity * out_quantity) / total_output
                
                if flow_quantity > 0:
                    flows.append((source_addr, target_addr, flow_quantity, tx_hash))
    
    return flows


def aggregate_flows(flows: list) -> dict:
    """Aggregate flows between same source-target pairs, collecting tx hashes."""
    aggregated = defaultdict(lambda: {'quantity': 0, 'tx_hashes': set()})
    for source, target, quantity, tx_hash in flows:
        aggregated[(source, target)]['quantity'] += quantity
        aggregated[(source, target)]['tx_hashes'].add(tx_hash)
    return aggregated


def create_vertical_sankey(flows: dict, title: str = "Token Movement Flow") -> go.Figure:
    """
    Create a vertical Sankey diagram (bottom to top).
    
    In a vertical Sankey:
    - Sources are at the bottom
    - Targets are at the top
    - Flows go upward
    """
    # Build node list - we need unique nodes
    nodes = set()
    for (source, target), _ in flows.items():
        nodes.add(source)
        nodes.add(target)
    
    node_list = sorted(list(nodes))
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}
    
    # Calculate node positions for vertical layout
    # Determine which nodes are primarily sources vs targets
    source_counts = defaultdict(float)
    target_counts = defaultdict(float)
    
    for (source, target), flow_data in flows.items():
        quantity = flow_data['quantity']
        source_counts[source] += quantity
        target_counts[target] += quantity
    
    # Calculate net flow direction for each node
    # Positive = more outgoing (source-like), Negative = more incoming (target-like)
    node_flow_balance = {}
    for node in node_list:
        outgoing = source_counts.get(node, 0)
        incoming = target_counts.get(node, 0)
        node_flow_balance[node] = outgoing - incoming
    
    # Sort nodes by their flow balance to create layers
    sorted_nodes = sorted(node_list, key=lambda n: node_flow_balance[n], reverse=True)
    
    # Create shortened labels for display
    short_labels = [shorten_address(node) for node in node_list]
    
    # Prepare source, target, value lists
    # Swap source and target to make flow go from top to bottom
    sources = []
    targets = []
    values = []
    hover_texts = []
    
    for (source, target), flow_data in flows.items():
        quantity = flow_data['quantity']
        tx_hashes = flow_data['tx_hashes']
        
        # Swap: original targets become sources (top), original sources become targets (bottom)
        sources.append(node_to_idx[target])
        targets.append(node_to_idx[source])
        values.append(quantity)
        
        # Build hover text with tx hashes
        tx_list = list(tx_hashes)
        if len(tx_list) <= 3:
            tx_display = '<br>'.join([f"  {h[:16]}..." for h in tx_list])
        else:
            tx_display = '<br>'.join([f"  {h[:16]}..." for h in tx_list[:3]])
            tx_display += f'<br>  ... and {len(tx_list) - 3} more'
        
        hover_text = (
            f"From: {shorten_address(source)}<br>"
            f"To: {shorten_address(target)}<br>"
            f"Amount: {quantity:,.0f}<br>"
            f"Transactions ({len(tx_list)}):<br>{tx_display}"
        )
        hover_texts.append(hover_text)
    
    # Normalize values for better visualization (use log scale for very large differences)
    max_val = max(values) if values else 1
    min_val = min(values) if values else 0
    
    # Generate colors for links based on flow magnitude
    import math
    colors = []
    for v in values:
        # Normalize to 0-1 range using log scale for better distribution
        if max_val > min_val:
            log_min = math.log10(min_val + 1)
            log_max = math.log10(max_val + 1)
            log_v = math.log10(v + 1)
            normalized = (log_v - log_min) / (log_max - log_min) if log_max > log_min else 0.5
        else:
            normalized = 0.5
        
        # Color gradient from light blue to dark blue
        r = int(100 + (1 - normalized) * 100)
        g = int(100 + (1 - normalized) * 100)
        b = int(200 + (1 - normalized) * 55)
        colors.append(f'rgba({r}, {g}, {b}, 0.6)')
    
    # Create node colors
    node_colors = []
    for node in node_list:
        balance = node_flow_balance.get(node, 0)
        if balance > 0:
            # Net source - more outgoing (green)
            node_colors.append('rgba(50, 150, 80, 0.9)')
        elif balance < 0:
            # Net sink - more incoming (orange)
            node_colors.append('rgba(200, 100, 50, 0.9)')
        else:
            # Balanced (blue)
            node_colors.append('rgba(100, 150, 200, 0.9)')
    
    # Create the Sankey diagram with vertical orientation
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        orientation='v',  # Vertical orientation
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color='rgba(50, 50, 50, 0.8)', width=1),
            label=short_labels,
            color=node_colors,
            hovertemplate='%{label}<br>Total Flow: %{value:,.0f}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors,
            customdata=hover_texts,
            hovertemplate='%{customdata}<extra></extra>'
        )
    )])
    
    fig.update_layout(
        font=dict(size=10, color='#333'),
        paper_bgcolor='rgba(248, 248, 255, 1)',
        plot_bgcolor='rgba(248, 248, 255, 1)',
        height=1200,
        width=1200,
        margin=dict(t=80, l=50, r=50, b=50)
    )
    
    return fig


def format_quantity(qty: float) -> str:
    """Format large quantities for readability."""
    if qty >= 1e15:
        return f"{qty/1e15:.2f}Q"
    elif qty >= 1e12:
        return f"{qty/1e12:.2f}T"
    elif qty >= 1e9:
        return f"{qty/1e9:.2f}B"
    elif qty >= 1e6:
        return f"{qty/1e6:.2f}M"
    elif qty >= 1e3:
        return f"{qty/1e3:.2f}K"
    else:
        return f"{qty:.0f}"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate a Sankey diagram of token flows for a specific date.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python token_flow_sankey.py                    # Uses yesterday's date (UTC)
    python token_flow_sankey.py --date 2025-12-05  # Uses specified date
        """
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date in YYYY-MM-DD format (UTC). Defaults to yesterday if not provided.'
    )
    return parser.parse_args()


def get_default_date() -> str:
    """Get yesterday's date in UTC as YYYY-MM-DD string."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def validate_date(date_str: str) -> bool:
    """Validate that a date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def main():
    args = parse_args()
    
    # Determine target date
    if args.date:
        if not validate_date(args.date):
            print(f"Error: Invalid date format '{args.date}'. Please use YYYY-MM-DD format.")
            return
        target_date = args.date
    else:
        target_date = get_default_date()
    
    print(f"Generating Sankey diagram for date: {target_date} (UTC)")
    
    # Path to SQL file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'token_transactions.sql')
    
    print(f"Querying database using: {sql_file}")
    transactions = load_transactions_from_db(sql_file, target_date)
    print(f"Loaded {len(transactions)} transactions")
    
    if not transactions:
        print(f"No transactions found for {target_date}. Exiting.")
        return
    
    # Extract flows
    flows = extract_flows(transactions)
    print(f"Extracted {len(flows)} individual flows")
    
    # Aggregate flows between same address pairs
    aggregated_flows = aggregate_flows(flows)
    print(f"Aggregated to {len(aggregated_flows)} unique address pairs")
    
    # No filtering - include all flows regardless of size
    # Previously we filtered small flows, but this excluded important small transfers
    filtered_flows = aggregated_flows
    print(f"Including all {len(filtered_flows)} flows (no filtering)")
    
    # Create the Sankey diagram
    fig = create_vertical_sankey(
        filtered_flows,
        title=""
    )
    
    # Create output directory if it doesn't exist
    out_dir = os.path.join(script_dir, 'out')
    os.makedirs(out_dir, exist_ok=True)
    
    # Save as PNG image with date in filename
    output_png = os.path.join(out_dir, f'token_flow_sankey_{target_date}.png')
    fig.write_image(output_png, scale=2)
    print(f"Diagram saved to: {output_png}")
    
    # Print summary statistics
    print("\n--- Flow Summary ---")
    sorted_flows = sorted(aggregated_flows.items(), key=lambda x: x[1]['quantity'], reverse=True)
    print("\nTop 10 largest flows:")
    for (source, target), flow_data in sorted_flows[:10]:
        print(f"  {shorten_address(source)} → {shorten_address(target)}: {format_quantity(flow_data['quantity'])} ({len(flow_data['tx_hashes'])} txs)")


if __name__ == "__main__":
    main()
