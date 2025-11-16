# auto_post_wp_fixed.py
"""
Clean, email-only entrypoint for the project. This file is a replacement for a previous
`auto_post_wp.py` that was refactored to use Post-by-Email.
"""

import os
import time
import json
import logging
from dotenv import load_dotenv
import re
import requests

# --- Google GenAI (Gemini) client
from google import genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

try:
    load_dotenv()
except Exception:
    logging.debug("No .env loaded; relying on environment variables")

GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
WP_EMAIL_ADDRESS = os.getenv("WP_EMAIL_ADDRESS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "paxep16902@agenra.com")  # SendGrid verified sender

if not GENAI_API_KEY:
    logging.error("Missing GEMINI_API_KEY")
    raise SystemExit(1)

if not SENDGRID_API_KEY:
    logging.error("Missing SENDGRID_API_KEY")
    raise SystemExit(1)

client = genai.Client(api_key=GENAI_API_KEY)


def choose_topic(max_retries=3, model="gemini-2.0-flash"):
    prompt = """You are an expert technical content strategist for a developer blog. Generate ONE fresh, compelling blog topic (6-12 words) that appeals to software developers and engineers.
Choose randomly from the following categories and then randomly from the subtopics within each category.:
DO NOT repeat topics from previous posts.
TOPIC DIVERSITY REQUIREMENTS:
- Rotate through these technical categories systematically:
  1. Programming Languages (new features, best practices, comparisons)
  2. Frameworks & Libraries (React, Vue, Angular, Spring, Django, etc.)
  3. Databases & Data Engineering (SQL, NoSQL, optimization, data modeling)
  4. DevOps & Infrastructure (Docker, Kubernetes, CI/CD, cloud platforms)
  5. System Design & Architecture (microservices, patterns, scalability)
  6. Performance & Optimization (caching, load balancing, monitoring)
  7. Security & Best Practices (authentication, encryption, vulnerabilities)
  8. Emerging Tech & Tools (AI/ML, blockchain, new dev tools, trends)
  9. Software Engineering Practices (testing, debugging, code quality)
  10. Career & Productivity (learning paths, team collaboration, workflows)

CRITERIA:
- Must be practical and actionable for working developers
- Avoid basic/introductory topics unless there's a novel angle
- Include both foundational concepts and cutting-edge technologies
- Balance between depth topics and broad appeal
- Ensure topics are evergreen enough to remain relevant
- Focus on problems developers actually face

Return ONLY the topic/title as plain text with no additional commentary."""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=40),
            )
            text = getattr(response, "text", None) or str(response)
            topic = next((ln.strip().strip('"').strip("'") for ln in text.splitlines() if ln.strip()), "")
            if topic:
                return topic
        except Exception:
            logging.debug("Topic gen attempt failed", exc_info=True)
        time.sleep(1)
    return f"Developer trends and tooling — {time.strftime('%Y-%m-%d')}"


def generate_post(topic, model="gemini-2.0-flash", max_output_tokens=1200):
    prompt = f"""Write a 500-1000 word blog post about: {topic}
Create content that is INTERESTING, UNDERSTANDABLE, HELPFUL, and CURIOUS for developers. Write in an engaging, conversational tone that feels like one developer explaining something cool to another.

Output ONLY the raw blog post text in PLAIN TEXT format. Use these formatting guidelines:
- Double line breaks between paragraphs
- Use #### Header for section headings (e.g., #### Why This Matters)
- Use *text* for emphasis/bold (e.g., *important concept*)
- For lists, use bullet points with • or numbers like 1. 2. 3.
- For code blocks, use triple backticks with language name:
  ```python
  code here
  ```
- For inline code references, wrap with backticks like: `variable_name`

IMPORTANT RULES:
- DO NOT use HTML tags like <p>, <strong>, <h1>, etc.
- DO NOT use markdown double asterisks like **bold**
- DO NOT include any introductory text or explanations
- Start directly with the content
- Output PLAIN TEXT ONLY - no HTML tags at all

The output will be sent via email to WordPress Post-by-Email, which will parse the formatting and convert to proper HTML."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    text = getattr(response, "text", None) or str(response)
    text = text.strip()
    
    # Remove any HTML tags that might have been added despite instructions
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove any code fence artifacts
    if text.startswith("```"):
        text = re.sub(r'^```.*?\n', '', text)
        text = re.sub(r'\n```$', '', text)
    
    # Return plain text content
    return {
        "title": topic,
        "body_html": text,  # Plain text, kept as body_html for compatibility with publish_via_email
        "tags": [t.lower() for t in topic.split()[:4]]
    }


def run_basic_checks(post):
    if not (SENDGRID_API_KEY and WP_EMAIL_ADDRESS and SENDER_EMAIL):
        raise ValueError("SENDGRID_API_KEY, SENDER_EMAIL and WP_EMAIL_ADDRESS are required in environment")
    return True


def publish_via_email(post):
    run_basic_checks(post)
    title = post.get("title", "Untitled")
    body_html = post.get("body_html", "")
    
    # Strip HTML tags to send plain text (WordPress Post-by-Email works better with plain text)
    # WordPress will auto-convert line breaks to paragraphs
    body_plain = re.sub(r'<[^>]+>', '', body_html).strip()
    
    # Build email body
    email_body = body_plain

    # SendGrid API endpoint
    sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
    
    # Create SendGrid email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": WP_EMAIL_ADDRESS}],
                "subject": title
            }
        ],
        "from": {"email": SENDER_EMAIL},
        "content": [
            {
                "type": "text/plain",
                "value": email_body
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    logging.info("Sending email via SendGrid API")
    logging.info("Sending to: %s", WP_EMAIL_ADDRESS)
    logging.info("Subject: %s", title)
    logging.info("Body length (plain text): %d chars", len(email_body))
    logging.debug("First 200 chars of body: %s", email_body[:200])
    
    try:
        response = requests.post(sendgrid_url, json=payload, headers=headers)
        
        if response.status_code == 202:
            logging.info("✓ Email sent successfully via SendGrid")
            return {"post_title": title, "to": WP_EMAIL_ADDRESS}
        else:
            logging.error("SendGrid API error: %s - %s", response.status_code, response.text)
            raise Exception(f"SendGrid error: {response.status_code}")
    except Exception as e:
        logging.error("Error sending email: %s", e)
        raise


def main():
    logging.info("Starting auto-post (fixed) flow")
    topic = choose_topic()
    logging.info("Topic: %s", topic)
    post = generate_post(topic)
    logging.info("Generated post")
    result = publish_via_email(post)
    with open("publish_log.jsonl", "a") as f:
        f.write(json.dumps({"topic": topic, "result": result, "ts": int(time.time())}) + "\n")
    logging.info("Done. Result: %s", result)


if __name__ == "__main__":
    main()
