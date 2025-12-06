#!/usr/bin/env python3
"""
Twitter/X posting module for Midnight Traces bot.

Uses tweepy library with Twitter API v2 for posting tweets with images.

Required environment variables (in .env file):
    TWITTER_API_KEY        - API Key (Consumer Key)
    TWITTER_API_SECRET     - API Secret (Consumer Secret)
    TWITTER_ACCESS_TOKEN   - Access Token
    TWITTER_ACCESS_SECRET  - Access Token Secret
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def format_date_display(date: str) -> str:
    """
    Format date from YYYY-MM-DD to human-readable format like '05 Dec 2025'.
    
    Args:
        date: Date string in YYYY-MM-DD format
        
    Returns:
        Formatted date string
    """
    from datetime import datetime
    dt = datetime.strptime(date, '%Y-%m-%d')
    return dt.strftime('%d %b %Y')


def generate_tweet_text(
    date: str,
    transaction_count: int,
    unique_addresses: int,
    flow_count: int
) -> str:
    """
    Generate the tweet text for the daily NIGHT token flow post.
    
    Args:
        date: Date string in YYYY-MM-DD format
        transaction_count: Number of transactions processed
        unique_addresses: Number of unique addresses involved
        flow_count: Number of token flows (traces)
        
    Returns:
        Tweet text with stats and hashtags
    """
    formatted_date = format_date_display(date)
    
    return f"""The $NIGHT  traces for {formatted_date}

- Transactions: {transaction_count:,}
- Addresses: {unique_addresses:,}
- Traces: {flow_count:,}

@MidnightNtwrk @midnightfdn #Cardano"""


def get_twitter_credentials() -> dict | None:
    """
    Get Twitter API credentials from environment variables.
    
    Returns:
        Dictionary with credentials, or None if any are missing.
    """
    credentials = {
        'api_key': os.environ.get("TWITTER_API_KEY"),
        'api_secret': os.environ.get("TWITTER_API_SECRET"),
        'access_token': os.environ.get("TWITTER_ACCESS_TOKEN"),
        'access_secret': os.environ.get("TWITTER_ACCESS_SECRET"),
    }
    
    missing = [k for k, v in credentials.items() if not v]
    if missing:
        print(f"Error: Missing Twitter credentials: {', '.join(missing)}")
        print("Please set these in your .env file")
        return None
    
    return credentials


def post_to_twitter(
    image_path: str,
    date: str,
    transaction_count: int = 0,
    unique_addresses: int = 0,
    flow_count: int = 0
) -> bool:
    """
    Post the styled Sankey diagram to Twitter/X.
    
    Args:
        image_path: Path to the styled image to post
        date: Date string for the post caption
        transaction_count: Number of transactions processed
        unique_addresses: Number of unique addresses involved
        flow_count: Number of token flows (traces)
        
    Returns:
        True if posted successfully, False otherwise
    """
    import tweepy
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return False
    
    # Get credentials
    creds = get_twitter_credentials()
    if not creds:
        return False
    
    # Generate tweet text with stats
    tweet_text = generate_tweet_text(date, transaction_count, unique_addresses, flow_count)
    
    try:
        # Initialize Twitter API v1.1 client (for media upload)
        auth = tweepy.OAuthHandler(creds['api_key'], creds['api_secret'])
        auth.set_access_token(creds['access_token'], creds['access_secret'])
        api_v1 = tweepy.API(auth)
        
        # Initialize Twitter API v2 client (for creating tweets)
        client = tweepy.Client(
            consumer_key=creds['api_key'],
            consumer_secret=creds['api_secret'],
            access_token=creds['access_token'],
            access_token_secret=creds['access_secret']
        )
        
        # Upload media using v1.1 API (v2 doesn't support media upload directly)
        print(f"Uploading image: {image_path}")
        media = api_v1.media_upload(filename=image_path)
        print(f"Media uploaded successfully. Media ID: {media.media_id}")
        
        # Post tweet with media using v2 API
        print("Posting tweet...")
        response = client.create_tweet(
            text=tweet_text,
            media_ids=[media.media_id]
        )
        
        tweet_id = response.data['id']
        print(f"Tweet posted successfully!")
        print(f"Tweet ID: {tweet_id}")
        print(f"URL: https://twitter.com/i/status/{tweet_id}")
        
        return True
        
    except tweepy.TweepyException as e:
        print(f"Twitter API error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error posting to Twitter: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Twitter posting module')
    parser.add_argument('--test-post', action='store_true', help='Actually post a test tweet')
    parser.add_argument('--image', type=str, help='Path to image for test post')
    parser.add_argument('--date', type=str, default='2025-12-05', help='Date for test post')
    args = parser.parse_args()
    
    print("Twitter module loaded successfully.")
    print(f"\nSample tweet text:")
    print("-" * 40)
    print(generate_tweet_text(args.date, 85, 64, 76))
    print("-" * 40)
    
    # Check credentials
    print("\nChecking Twitter credentials...")
    creds = get_twitter_credentials()
    if creds:
        print("✓ All credentials found")
    
    # Test posting if requested
    if args.test_post and args.image:
        print(f"\nPosting test tweet with image: {args.image}")
        success = post_to_twitter(args.image, args.date, 85, 64, 76)
        if success:
            print("\n✓ Test post successful!")
        else:
            print("\n✗ Test post failed")
