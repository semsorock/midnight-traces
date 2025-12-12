#!/usr/bin/env python3
"""
Debug script to inspect Sankey flow data topology.
Prints detailed stats about sources, targets, and flow magnitudes.
"""

import os
from collections import defaultdict
import datetime
from token_flow_sankey import load_transactions_from_db, extract_flows, aggregate_flows, shorten_address, TOKEN_DECIMALS

# Use the same date as the user's manual run or default
TARGET_DATE = "2025-12-11"

def analyze_flows(flows_dict, max_flows=100):
    print(f"\nAnalyzing {len(flows_dict)} flows (showing top {max_flows})...")
    
    # Sort by quantity
    sorted_flows = sorted(flows_dict.items(), key=lambda x: x[1]['quantity'], reverse=True)
    top_flows = sorted_flows[:max_flows]
    
    # 1. Source/Target Analysis
    sources = defaultdict(int)
    targets = defaultdict(int)
    total_volume = 0
    
    for (s, t), data in top_flows:
        qty = data['quantity']
        sources[s] += 1
        targets[t] += 1
        total_volume += qty
        
    print(f"\nUnique Sources: {len(sources)}")
    print(f"Unique Targets: {len(targets)}")
    
    # 2. Fan-out / Fan-in Check
    print("\nTop Sources by Fan-out (destinations in top 100 flows):")
    for s, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {shorten_address(s)} -> {count} targets")
        
    print("\nTop Targets by Fan-in (sources in top 100 flows):")
    for t, count in sorted(targets.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {shorten_address(t)} <- {count} sources")

    # 3. Value Distribution Check
    print("\nTop 5 Flows by Volume:")
    for (s, t), data in top_flows[:5]:
        qty = data['quantity']
        pct = (qty / total_volume) * 100
        print(f"  {shorten_address(s)} -> {shorten_address(t)}: {qty:.2e} ({pct:.1f}%)")

    # 4. Self-Loop Check
    self_loops = [((s,t), d) for (s,t), d in top_flows if s == t]
    if self_loops:
        print(f"\nFound {len(self_loops)} Self-Loops:")
        for (s, t), data in self_loops:
             print(f"  {shorten_address(s)} -> {shorten_address(t)}: {data['quantity']:.2e}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'token_transactions.sql')
    
    print(f"Loading transactions for {TARGET_DATE}...")
    transactions = load_transactions_from_db(sql_file, TARGET_DATE)
    print(f"Loaded {len(transactions)} transactions")
    
    flows = extract_flows(transactions)
    aggregated = aggregate_flows(flows)
    
    analyze_flows(aggregated)

if __name__ == "__main__":
    main()
