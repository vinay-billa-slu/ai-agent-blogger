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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# --- Google GenAI (Gemini) client
from google import genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

try:
    load_dotenv()
except Exception:
    logging.debug("No .env loaded; relying on environment variables")

GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
WP_EMAIL_ADDRESS = os.getenv("WP_EMAIL_ADDRESS")

if not GENAI_API_KEY:
    logging.error("Missing GEMINI_API_KEY")
    raise SystemExit(1)

client = genai.Client(api_key=GENAI_API_KEY)


def choose_topic(max_retries=3, model="gemini-2.0-flash"):
    prompt = (
        "You are an expert content ideation assistant for developer blogs. "
        "Generate ONE concise blog topic/title (6-12 words) focused on developer and technical subjects. "
        "Return only the topic/title as plain text."
    )
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

Output ONLY the raw blog post text in HTML format. Use clear paragraph breaks eg <br> for newline <b> or <strong> for bold or strong etc. Do NOT include any markdown, code fences, or JSON unless needed for a code block"""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    text = getattr(response, "text", None) or str(response)
    text = text.strip()
    
    # Remove any markdown or code fence artifacts
    if text.startswith("```"):
        text = re.sub(r'^```.*?\n', '', text)
        text = re.sub(r'\n```$', '', text)
    
    # Return plain text content (WordPress Post-by-Email will auto-format)
    return {
        "title": topic,
        "body_html": text,  # Actually plain text, kept as body_html for compatibility
        "tags": [t.lower() for t in topic.split()[:4]]
    }


def run_basic_checks(post):
    if not (GMAIL_USER and GMAIL_APP_PASSWORD and WP_EMAIL_ADDRESS):
        raise ValueError("GMAIL_USER, GMAIL_APP_PASSWORD and WP_EMAIL_ADDRESS are required in environment")
    return True


def publish_via_email(post):
    run_basic_checks(post)
    title = post.get("title", "Untitled")
    body_html = post.get("body_html", "")
    
    # Strip HTML tags to send plain text (WordPress Post-by-Email works better with plain text)
    # WordPress will auto-convert line breaks to paragraphs
    body_plain = re.sub(r'<[^>]+>', '', body_html).strip()
    
    # Build email body
    email_body = ""
    email_body += body_plain

    # Create simple text email (Post-by-Email prefers plain text)
    msg = MIMEText(email_body, "plain", "utf-8")
    msg["Subject"] = title
    msg["From"] = GMAIL_USER
    msg["To"] = WP_EMAIL_ADDRESS

    logging.info("Connecting to smtp.gmail.com:465")
    logging.info("Sending to: %s", WP_EMAIL_ADDRESS)
    logging.info("Subject: %s", title)
    logging.info("Body length (plain text): %d chars", len(email_body))
    logging.debug("First 200 chars of body: %s", email_body[:200])
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info("✓ Email sent successfully")
        return {"post_title": title, "to": WP_EMAIL_ADDRESS}
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP auth failed")
        raise
    except Exception as e:
        logging.error("SMTP error: %s", e)
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
