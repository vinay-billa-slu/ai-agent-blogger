#!/usr/bin/env python3
"""Test that content is being generated properly."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
with open('.env', 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value.strip('"').strip("'")

from google import genai
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GENAI_API_KEY)

topic = "Advanced Python Context Managers: Best Practices"
print(f"\n{'='*80}")
print(f"Testing content generation for: {topic}")
print(f"{'='*80}\n")

# Test fallback prompt
prompt = f"""
Write a 700-900 word blog post about: {topic}
Use professional, friendly tone. Include introduction, main points, and conclusion.
Format with clear sections and paragraphs. No JSON, no markdown, plain text only.
"""

logging.info("Calling Gemini API...")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config=genai.types.GenerateContentConfig(max_output_tokens=1200)
)

body_text = getattr(response, "text", None) or str(response)
body_text = body_text.strip()

print(f"✓ Generated {len(body_text)} characters\n")
print("CONTENT PREVIEW (first 400 chars):")
print("-" * 80)
print(body_text[:400])
print("...")
print("-" * 80)

# Convert to HTML
body_html = ""
for para in body_text.split('\n\n'):
    para = para.strip()
    if para:
        if para.startswith('-') or para.startswith('*'):
            lines = para.split('\n')
            body_html += "<ul>"
            for line in lines:
                line = line.strip().lstrip('-').lstrip('*').strip()
                if line:
                    body_html += f"<li>{line}</li>"
            body_html += "</ul>"
        else:
            body_html += f"<p>{para}</p>"

print(f"\n✓ HTML version: {len(body_html)} characters")
print("\nHTML PREVIEW (first 300 chars):")
print("-" * 80)
print(body_html[:300])
print("...")
print("-" * 80)
print(f"\n✅ SUCCESS! Content generation is working!\n")
