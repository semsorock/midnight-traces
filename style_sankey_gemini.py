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


def style_sankey_diagram():
    """Load the Sankey diagram and apply futuristic styling via Gemini API."""
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, 'out', 'token_flow_sankey.png')
    output_path = os.path.join(script_dir, 'out', 'token_flow_sankey_styled.png')
    
    # Load the source image
    print(f"Loading source image: {input_path}")
    source_image = Image.open(input_path)
    
    # Detailed styling prompt
    prompt = """
    Transform this Sankey diagram into a stunning, futuristic, deep space, cosmic data visualization with a high-tech, bioluminescent aesthetic.

    STYLE REQUIREMENTS:
    - Background: A dark, starry void set in deep space with subtle nebula dust and faint, glowing constellation patterns.
    - Flow/Links: Replace all flow/link colors with ethereal, translucent energy streams and wispy fiber-optic filaments. These should display a gradient of vibrant neon colors (electric blue, magenta, cyan, and deep purple).
    - Flow Effects: Add ethereal glow effects and bloom effects around the flowing links. Apply particle/sparkle effects along the flow paths.
    - Nodes: The connection nodes (label boxes) should be glowing, neon-lit pill-shaped bars. Apply a glassmorphism effect to the node label boxes with subtle transparency.
    - Overall Aesthetic: High-tech, futuristic data visualization, premium feel, bioluminescent, and cinematic, with volumetric lighting and intricate glowing constellations connecting the data points. 8k resolution, sci-fi interface style.

    IMPORTANT:
    - Preserve: Keep the overall structure and layout of the Sankey diagram intact.
    - Data Integrity: Preserve all text labels and the readable structure of the Sankey diagram.
    """
    
    # Initialize Gemini client with API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    client = genai.Client(api_key=api_key)
    
    print("Sending to Gemini Image API...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        # model="gemini-2.5-flash-image",
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
    result = style_sankey_diagram()
    if result:
        print(f"\nSuccess! Open {result} to view the styled diagram.")
    else:
        print("\nFailed to generate styled image.")
