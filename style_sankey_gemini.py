#!/usr/bin/env python3
"""
Sankey Diagram Stylizer using Gemini 3 Pro Image API

Transforms the generated Sankey diagram into a futuristic, space-themed
visualization using the Gemini 3 Pro Image model (Nano Banana Pro).
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Load environment variables from .env file
load_dotenv()


def style_sankey_diagram(target_date: str | None = None) -> str | None:
    """
    Load the Sankey diagram and apply futuristic styling via Gemini API.
    
    Args:
        target_date: Date in YYYY-MM-DD format. If None, uses generic naming.
        
    Returns:
        Path to styled image, or None if generation failed.
    """
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if target_date:
        input_path = os.path.join(script_dir, 'out', f'token_flow_sankey_{target_date}.png')
        output_path = os.path.join(script_dir, 'out', f'token_flow_sankey_styled_{target_date}.png')
    else:
        input_path = os.path.join(script_dir, 'out', 'token_flow_sankey.png')
        output_path = os.path.join(script_dir, 'out', 'token_flow_sankey_styled.png')
    
    # Verify input exists
    if not os.path.exists(input_path):
        print(f"Error: Source image not found: {input_path}")
        return None
    
    # Load the source image
    print(f"Loading source image: {input_path}")
    source_image = Image.open(input_path)
    
    # Detailed styling prompt
    prompt = """
    CRITICAL INSTRUCTION: STRICT TOPOLOGY PRESERVATION
You are functioning as a style-transfer engine, not a data generator. You must maintain a 1:1 structural mapping with the original image.
1. DO NOT create new connections, flows, or links.
2. DO NOT bridge gaps between nodes that are not connected in the source.
3. Apply effects ONLY to the exact pixel coordinates of existing flows.

TASK:
Reskin this Sankey diagram into a futuristic, deep space, cosmic data visualization.

VISUAL STYLE GUIDE:
- Flows (Data Layers): Transform existing flow paths into ethereal, translucent energy streams with wispy fiber-optic textures. Use a vibrant neon gradient (electric blue, magenta, cyan, deep purple). Add bloom and subtle particle effects *strictly within the boundaries* of the existing flows.
- Nodes (Labels): Convert label boxes into glowing, neon-lit pill-shaped glass bars. distinct from the background.
- Background (Void): A dark, starry void. faint nebula dust.
- Background Detail: Faint constellation patterns in the *far background only*. These patterns must be unconnected to the main data flows and significantly dimmer than the data to avoid confusion.

AESTHETIC:
High-tech, deep space,bioluminescent, cinematic, 8k resolution, sci-fi interface.

FINAL CHECK:
Ensure the output is topologically identical to the input. No new data paths.
"""
    
    # Initialize Gemini client with API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    client = genai.Client(api_key=api_key)
    
    print("Sending to Gemini Image API...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt, source_image],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="2K"
            ),
        )
    )
    
    # Process response
    for part in response.parts:
        if part.text is not None:
            print(f"Model response: {part.text}")
        elif image := part.as_image():
            image.save(output_path)
            print(f"Styled image saved to: {output_path}")
            return output_path
    
    print("Warning: No image was generated in the response")
    return None


if __name__ == "__main__":
    import argparse
    from datetime import datetime, timedelta, timezone
    
    def get_default_date() -> str:
        """Get yesterday's date in UTC as YYYY-MM-DD string."""
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    parser = argparse.ArgumentParser(
        description='Apply Gemini styling to a Sankey diagram.'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date in YYYY-MM-DD format (UTC). Defaults to yesterday.'
    )
    args = parser.parse_args()
    
    target_date = args.date or get_default_date()
    result = style_sankey_diagram(target_date)
    
    if result:
        print(f"\nSuccess! Open {result} to view the styled diagram.")
    else:
        print("\nFailed to generate styled image.")

