#!/usr/bin/env python3
"""
Midnight Traces Pipeline

Orchestrates the full Twitter bot workflow:
1. Load NIGHT token transactions from DB for target date
2. Generate Sankey diagram visualization
3. Apply Gemini styling
4. Post to Twitter (TODO)

Usage:
    python pipeline.py                    # Uses yesterday's date (UTC)
    python pipeline.py --date 2025-12-05  # Uses specified date
    python pipeline.py --skip-styling     # Skip Gemini styling step
    python pipeline.py --skip-twitter     # Skip Twitter posting (default for now)
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from token_flow_sankey import generate_sankey, MAX_TX_COUNT_DEFAULT
from style_sankey_gemini import style_sankey_diagram
from twitter import post_to_twitter


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


def run_pipeline(
    target_date: str,
    skip_styling: bool = False,
    skip_twitter: bool = True,
    max_tx_count: int = MAX_TX_COUNT_DEFAULT
) -> dict:
    """
    Run the full Midnight Traces pipeline.
    
    Args:
        target_date: Date in YYYY-MM-DD format (UTC)
        skip_styling: If True, skip the Gemini styling step
        skip_twitter: If True, skip posting to Twitter (default True for now)
        max_tx_count: Maximum number of top transactions to visualize
        
    Returns:
        Dictionary with paths to generated files and status
    """
    result = {
        'date': target_date,
        'sankey_path': None,
        'styled_path': None,
        'twitter_posted': False,
        'stats': {
            'transaction_count': 0,
            'unique_addresses': 0,
            'flow_count': 0,
            'total_tokens_moved': 0
        },
        'errors': []
    }
    
    print(f"\n{'='*60}")
    print(f"  Midnight Traces Pipeline - {target_date}")
    print(f"{'='*60}\n")
    
    # Stage 1 & 2: Generate Sankey diagram (includes DB query)
    print("📊 Stage 1: Generating Sankey diagram...")
    try:
        sankey_result = generate_sankey(target_date, max_tx_count=max_tx_count)
        if sankey_result:
            result['sankey_path'] = sankey_result['path']
            result['stats'] = {
                'transaction_count': sankey_result['transaction_count'],
                'unique_addresses': sankey_result['unique_addresses'],
                'flow_count': sankey_result['flow_count'],
                'total_tokens_moved': sankey_result['total_tokens_moved']
            }
            print(f"   ✓ Sankey diagram saved: {sankey_result['path']}")
        else:
            result['errors'].append("No transactions found for this date")
            print(f"   ✗ No transactions found for {target_date}")
            return result
    except Exception as e:
        result['errors'].append(f"Sankey generation failed: {e}")
        print(f"   ✗ Error: {e}")
        return result
    
    # Stage 3: Apply Gemini styling
    if not skip_styling:
        print("\n🎨 Stage 2: Applying Gemini styling...")
        try:
            styled_path = style_sankey_diagram(target_date)
            if styled_path:
                result['styled_path'] = styled_path
                print(f"   ✓ Styled diagram saved: {styled_path}")
            else:
                result['errors'].append("Gemini styling returned no image")
                print("   ✗ No styled image generated")
        except Exception as e:
            result['errors'].append(f"Gemini styling failed: {e}")
            print(f"   ✗ Error: {e}")
    else:
        print("\n🎨 Stage 2: Skipping Gemini styling (--skip-styling)")
    
    # Stage 4: Post to Twitter
    if not skip_twitter:
        # Check if styling failed (requested but no result)
        if not skip_styling and not result['styled_path']:
            print("\n🐦 Stage 3: Aborting Twitter post because styling failed")
            result['errors'].append("Aborted Twitter post due to styling failure")
        else:
            print("\n🐦 Stage 3: Posting to Twitter...")
            image_to_post = result['styled_path'] or result['sankey_path']
            if image_to_post:
                try:
                    posted = post_to_twitter(
                        image_to_post,
                        target_date,
                        transaction_count=result['stats']['transaction_count'],
                        unique_addresses=result['stats']['unique_addresses'],
                        flow_count=result['stats']['flow_count'],
                        total_tokens_moved=result['stats']['total_tokens_moved']
                    )
                    result['twitter_posted'] = posted
                    if posted:
                        print("   ✓ Posted to Twitter")
                    else:
                        print("   ✗ Twitter posting not yet implemented")
                except Exception as e:
                    result['errors'].append(f"Twitter posting failed: {e}")
                    print(f"   ✗ Error: {e}")
    else:
        print("\n🐦 Stage 3: Skipping Twitter (--skip-twitter)")
    
    # Summary
    print(f"\n{'='*60}")
    print("  Pipeline Complete!")
    print(f"{'='*60}")
    if result['sankey_path']:
        print(f"  📊 Sankey: {result['sankey_path']}")
    if result['styled_path']:
        print(f"  🎨 Styled: {result['styled_path']}")
    stats = result['stats']
    from token_flow_sankey import format_quantity
    print(f"  📈 Stats: {stats['transaction_count']} txs, {stats['unique_addresses']} addresses, {stats['flow_count']} flows, {format_quantity(stats['total_tokens_moved'])} $NIGHT moved")
    if result['errors']:
        print(f"  ⚠️  Warnings: {len(result['errors'])}")
        for err in result['errors']:
            print(f"      - {err}")
    print()
    
    return result


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Midnight Traces Pipeline - Generate and post NIGHT token flow visualizations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python pipeline.py                    # Uses yesterday's date (UTC)
    python pipeline.py --date 2025-12-05  # Uses specified date
    python pipeline.py --skip-styling     # Skip Gemini styling step
    python pipeline.py --post-twitter     # Enable Twitter posting
    python pipeline.py --check-ready      # Check if all credentials are configured
        """
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date in YYYY-MM-DD format (UTC). Defaults to yesterday.'
    )
    parser.add_argument(
        '--skip-styling',
        action='store_true',
        help='Skip the Gemini image styling step.'
    )
    parser.add_argument(
        '--post-twitter',
        action='store_true',
        default=False,
        help='Enable posting to Twitter (default: disabled).'
    )
    parser.add_argument(
        '--check-ready',
        action='store_true',
        help='Check if all credentials are configured and exit.'
    )
    parser.add_argument(
        '--max-tx-count',
        type=int,
        default=MAX_TX_COUNT_DEFAULT,
        help=f'Maximum top transactions to visualize (default: {MAX_TX_COUNT_DEFAULT}).'
    )
    return parser.parse_args()


def check_ready() -> bool:
    """
    Check if all required credentials are configured.
    
    Returns:
        True if all credentials are ready, False otherwise.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🔍 Checking pipeline readiness...\n")
    
    all_ready = True
    
    # Check Gemini API
    print("📦 Gemini API (for image styling):")
    gemini_key = os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        print(f"   ✓ GOOGLE_API_KEY is set ({gemini_key[:8]}...)")
    else:
        print("   ✗ GOOGLE_API_KEY is NOT set")
        all_ready = False
    
    # Check Twitter API
    print("\n🐦 Twitter API (for posting):")
    twitter_vars = {
        'TWITTER_API_KEY': 'API Key',
        'TWITTER_API_SECRET': 'API Secret',
        'TWITTER_ACCESS_TOKEN': 'Access Token',
        'TWITTER_ACCESS_SECRET': 'Access Secret',
    }
    
    for var, name in twitter_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"   ✓ {var} is set ({value[:8]}...)")
        else:
            print(f"   ✗ {var} is NOT set")
            all_ready = False
    
    # Check database connection
    print("\n📊 Database (for transaction data):")
    try:
        from token_flow_sankey import DB_CONNECTION_STRING
        if DB_CONNECTION_STRING:
            print(f"   ✓ DB_CONNECTION_STRING is configured")
        else:
            print("   ✗ DB_CONNECTION_STRING is NOT set")
            all_ready = False
    except Exception as e:
        print(f"   ✗ Error checking database config: {e}")
        all_ready = False
    
    # Summary
    print("\n" + "="*50)
    if all_ready:
        print("✅ All credentials configured! Ready to run.")
        print("\nTo post to Twitter, run:")
        print("  python pipeline.py --post-twitter")
    else:
        print("❌ Some credentials are missing. Check your .env file.")
        print("\nSee .env.example for required variables.")
    print("="*50 + "\n")
    
    return all_ready


def main():
    args = parse_args()
    
    # Check ready mode
    if args.check_ready:
        check_ready()
        return
    
    # Determine target date
    if args.date:
        if not validate_date(args.date):
            print(f"Error: Invalid date format '{args.date}'. Please use YYYY-MM-DD format.")
            sys.exit(1)
        target_date = args.date
    else:
        target_date = get_default_date()
    
    # If posting to Twitter, verify credentials first
    if args.post_twitter:
        from twitter import get_twitter_credentials
        if not get_twitter_credentials():
            print("\nRun 'python pipeline.py --check-ready' to see all missing credentials.")
            sys.exit(1)
    
    # Run the pipeline
    result = run_pipeline(
        target_date=target_date,
        skip_styling=args.skip_styling,
        skip_twitter=not args.post_twitter,  # Invert: --post-twitter means don't skip
        max_tx_count=args.max_tx_count
    )
    
    # Exit with error code if there were failures
    if result['errors'] and not result['sankey_path']:
        sys.exit(1)


if __name__ == "__main__":
    main()

