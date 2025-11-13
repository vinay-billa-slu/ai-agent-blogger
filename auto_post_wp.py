# auto_post_wp.py
"""
Auto-generate blog posts using Google Gemini (GenAI SDK) and publish to WordPress via XML-RPC API.
- Compatible with both WordPress.com and self-hosted WordPress
- Generates a draft (default) so you can review before publishing.
- Logs results to publish_log.jsonl
"""

import os
import time
import json
import logging
from requests.auth import HTTPBasicAuth
import requests
from dotenv import load_dotenv
import xmlrpc.client
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Google GenAI (Gemini) client
# install: pip install google-genai
from google import genai

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Load environment variables from .env file (for local development)
try:
    load_dotenv()  # Loads .env from the same directory or parent directories
except ImportError:
    logging.warning("python-dotenv not installed. Skipping .env file loading.")

# Config (read from env secrets)
WP_SITE = os.getenv("WP_SITE", "https://vinaybilla5.wordpress.com")  # no trailing slash
WP_USER = os.getenv("WP_USER")           # WordPress username (or email)
WP_APP_PASS = os.getenv("WORDPRESS_TOKEN")   # Application password (24-char)
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")  # Google GenAI API key

# Email posting (Post by Email feature)
GMAIL_USER = os.getenv("GMAIL_USER")           # Gmail account (e.g., user@gmail.com)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Gmail app password
WP_EMAIL_ADDRESS = os.getenv("WP_EMAIL_ADDRESS")      # WordPress Post by Email address

if not WP_USER or not WP_APP_PASS or not GENAI_API_KEY:
    logging.error("Missing one or more required environment variables: WP_USER, WORDPRESS_TOKEN, GEMINI_API_KEY")
    raise SystemExit(1)

# Initialize genai client with API key
# For google-genai >= 1.0, pass api_key to Client constructor
client = genai.Client(api_key=GENAI_API_KEY)

def choose_topic(max_retries=3, model="gemini-2.0-flash"):
    """
    Dynamically generate a single developer-focused topic/title using the GenAI model.
    Returns a short topic string suitable as a blog title (roughly 6-12 words).
    Falls back to a deterministic default if generation fails.
    """
    prompt = """
You are an expert content ideation assistant for developer blogs. Generate ONE concise blog topic/title (6-12 words) focused exclusively on developer and technical subjects such as programming languages, AI/ML, frameworks, system design, DSA, optimization, performance, security, load balancing, latency, observability, developer tools, testing, deployment, DevOps, cloud, or problem-solving. Do NOT return a list. Return only the topic/title as plain text, no JSON, no bullets, no explanation. Keep it original and specific.
"""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=40)
            )
            text = getattr(response, "text", None) or str(response)
            text = text.strip()
            # take only the first non-empty line
            topic = ""
            for line in text.splitlines():
                line = line.strip()
                if line:
                    topic = line
                    break
            # strip common surrounding quotes
            topic = topic.strip('"').strip("'")
            # basic validation
            word_count = len(topic.split())
            if topic and 3 <= word_count <= 20 and len(topic) > 10:
                # quick keyword heuristic to ensure developer-focus
                keywords = [
                    "ai","ml","machine","learning","python","java","node","django","flask","fastapi",
                    "performance","security","latency","load","kubernetes","docker","devops","algorithm",
                    "data structure","dsa","optimization","framework","testing","deployment","observability",
                    "cloud","scalability","database","sql","nosql"
                ]
                lowered = topic.lower()
                if any(k in lowered for k in keywords) or any(w in lowered for w in ["with","using","in","for","how","optim","secure","build","deploy"]):
                    return topic
            # otherwise retry
        except Exception as e:
            logging.warning("Topic generation attempt %s failed: %s", attempt+1, e)
        time.sleep(1)
    logging.warning("Falling back to deterministic default topic")
    # deterministic fallback derived from timestamp to avoid hardcoded list
    fallback = f"Developer trends and tooling — {time.strftime('%Y-%m-%d')}"
    return fallback

def generate_post(topic, model="gemini-2.0-flash", max_output_tokens=1200):
    logging.info("Generating post for topic: %s", topic)
    prompt = f"""
You are a professional Medium/WordPress writer. Write a 700-900 word article about: {topic}
Return ONLY valid JSON with these exact keys (no markdown, no extra text, just JSON):
{{
  "title": "string",
  "subtitle": "string, one-line summary",
  "body_html": "string with HTML tags like <h2>, <p>, <ul>/<li>",
  "tags": ["array", "of", "tags"]
}}
Make the article original, friendly, and actionable.
"""
    # Use the genai SDK to generate text
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens)
    )
    # The SDK returns objects; response.text or str(response) contains the model output
    text = getattr(response, "text", None) or str(response)
    text = text.strip()
    
    # Try to extract JSON from markdown code blocks if present
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    
    # attempt to parse JSON from the model
    try:
        data = json.loads(text)
        logging.info("✓ Successfully parsed JSON response from Gemini")
    except json.JSONDecodeError as e:
        # fallback: Generate full content using a simpler approach
        logging.warning("JSON parsing failed (%s), generating content with fallback prompt", str(e)[:50])
        
        # Make a second attempt with simpler prompt
        fallback_prompt = f"""
Write a 700-900 word blog post about: {topic}
Use professional, friendly tone. Include introduction, main points, and conclusion.
Format with clear sections and paragraphs. No JSON, no markdown, plain text only.
"""
        try:
            response2 = client.models.generate_content(
                model=model,
                contents=fallback_prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens)
            )
            body_text = getattr(response2, "text", None) or str(response2)
            body_text = body_text.strip()
            
            # Convert plain text to HTML paragraphs
            body_html = ""
            for para in body_text.split('\n\n'):
                para = para.strip()
                if para:
                    # Convert bullet points to HTML lists
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
            
            data = {
                "title": topic,
                "subtitle": f"A detailed guide on {topic}",
                "body_html": body_html,
                "tags": [word.lower() for word in topic.split()[:3]]
            }
            logging.info("✓ Generated content using fallback prompt")
        except Exception as fallback_error:
            logging.error("Fallback generation also failed: %s", fallback_error)
            # Last resort: create minimal post
            data = {
                "title": topic,
                "subtitle": f"Expert insights on {topic}",
                "body_html": f"<p>This article explores the key concepts, best practices, and practical applications of {topic} in modern development. Whether you're a beginner or an experienced developer, you'll find valuable insights and actionable takeaways.</p>",
                "tags": [word.lower() for word in topic.split()[:3]]
            }
    
    return data

def run_basic_checks(post):
    # Basic quality & safety checks — extend as needed
    if not post.get("body_html") or len(post.get("body_html","")) < 400:
        raise ValueError("Generated content too short")
    title = post.get("title","").lower()
    for banned in ["bomb","kill","hate","terror"]:
        if banned in title:
            raise ValueError("Unsafe or disallowed content in title")
    return True

def publish_to_wordpress(post, publish_status="draft"):
    """
    Publish to WordPress using XML-RPC API (compatible with WordPress.com and self-hosted).
    Tries multiple XML-RPC endpoints to find the correct one.
    """
    # Determine possible XML-RPC endpoints to try
    endpoints = []
    
    if "wordpress.com" in WP_SITE:
        # WordPress.com: try blog's own endpoint first, then main endpoint
        endpoints = [
            f"{WP_SITE}/xmlrpc.php",  # Blog's own endpoint
            "https://wordpress.com/xmlrpc.php",  # Main WordPress.com endpoint
        ]
    else:
        # Self-hosted WordPress
        endpoints = [f"{WP_SITE}/xmlrpc.php"]
    
    # Prepare the post data in WordPress format
    post_data = {
        "post_title": post.get("title"),
        "post_content": f"<h2>{post.get('subtitle','')}</h2>\n{post.get('body_html')}",
        "post_status": "draft" if publish_status == "draft" else "publish",
        "post_type": "post",
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    last_error = None
    
    for xmlrpc_url in endpoints:
        try:
            logging.info("Attempting to publish via: %s", xmlrpc_url)
            server = xmlrpc.client.ServerProxy(xmlrpc_url, context=ssl_context)

            # First try blog IDs returned by wp.getUsersBlogs (most reliable)
            try:
                blogs = server.wp.getUsersBlogs(WP_USER, WP_APP_PASS)
            except Exception:
                blogs = []

            blog_ids_to_try = []
            for b in blogs:
                if isinstance(b, dict):
                    bid = b.get('blogid')
                else:
                    # some servers return objects with attributes
                    bid = getattr(b, 'blogid', None)
                if bid:
                    blog_ids_to_try.append(bid)

            # Fallback to common numeric ids
            blog_ids_to_try.extend([0, 1])

            # Try the collected blog IDs
            for blog_id in blog_ids_to_try:
                try:
                    post_id = server.metaWeblog.newPost(blog_id, WP_USER, WP_APP_PASS, post_data)
                    logging.info("✓ Post created successfully! ID: %s", post_id)
                    return {"post_id": post_id, "link": f"{WP_SITE}/?p={post_id}"}
                except xmlrpc.client.Fault as e:
                    last_error = str(e)
                    # Provide clearer guidance for 401 errors
                    if '401' in last_error:
                        logging.error("XML-RPC Fault 401 for blog_id %s: %s", blog_id, e)
                        logging.error("This account is authenticated but does not have permission to publish to that blog.")
                        logging.error("- Verify the blog is associated with the WP_USER account.")
                        logging.error("- Use the blog owner's WP_USER and app password, or add the user with an appropriate role (Editor/Author).")
                        logging.error("- Double-check the exact blog ID returned by server.wp.getUsersBlogs().")
                        raise
                    logging.debug("Blog ID %s failed: %s", blog_id, e)
                    continue

        except Exception as e:
            logging.debug("Endpoint %s failed: %s", xmlrpc_url, e)
            last_error = str(e)
            continue
    
    # If we get here, all attempts failed
    error_msg = f"Failed to publish post. Last error: {last_error}"
    logging.error(error_msg)
    logging.error("\nTroubleshooting tips:")
    logging.error("1. Verify credentials: python3 diagnose_wp.py")
    logging.error("2. Ensure blog is associated with %s account", WP_USER)
    logging.error("3. Check if XML-RPC is enabled in Settings → Writing")
    raise Exception(error_msg)

def publish_via_email(post, publish_status="draft"):
    """
    Publish to WordPress using Post by Email feature via Gmail SMTP.
    This is a fallback method when XML-RPC/REST API are unavailable.
    
    Requirements:
    - WordPress "Post by Email" feature enabled
    - Gmail account with app password configured
    - WP_EMAIL_ADDRESS set in .env (WordPress Post by Email address)
    
    Post by Email address format:
    - Go to WordPress Settings → Post by Email
    - Copy the "Post by Email address" (looks like: publish-abc123@vinaybilla5.wordpress.com)
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not WP_EMAIL_ADDRESS:
        raise ValueError(
            "Email posting requires: GMAIL_USER, GMAIL_APP_PASSWORD, WP_EMAIL_ADDRESS\n"
            "Please configure these in .env file and enable 'Post by Email' in WordPress settings."
        )
    
    logging.info("Publishing via Gmail Post by Email...")
    
    try:
        # Prepare email content
        # WordPress Post by Email uses subject as title, body as content
        title = post.get("title", "Untitled")
        body_html = post.get("body_html", "")
        subtitle = post.get("subtitle", "")
        
        # Clean up body_html: remove JSON artifacts and excessive whitespace
        # Remove markdown code fences
        body_html = body_html.replace("```json", "").replace("```", "")
        # Remove lines that look like JSON keys
        lines = []
        for line in body_html.split('\n'):
            stripped = line.strip()
            # Skip empty lines and JSON key patterns
            if not stripped:
                continue
            if any(k in stripped for k in ['"title":', '"subtitle":', '"body_html":', '"tags":', '"name":', '"app']):
                continue
            if stripped.startswith('"') and stripped.endswith('",') or stripped.endswith('":'):
                continue
            lines.append(line)
        
        body_html = '\n'.join(lines).strip()
        # Collapse excessive newlines
        while '\n\n\n' in body_html:
            body_html = body_html.replace('\n\n\n', '\n\n')
        
        # Build the email body
        # WordPress extracts first line as title, rest as content
        email_body = f"{title}\n\n"
        if subtitle:
            email_body += f"{subtitle}\n\n"
        email_body += body_html
        
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = GMAIL_USER
        msg["To"] = WP_EMAIL_ADDRESS
        
        # Attach both plain text and HTML versions
        text_part = MIMEText(email_body, "plain")
        html_part = MIMEText(email_body, "html")
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Connect to Gmail SMTP and send
        logging.info("Connecting to Gmail SMTP server...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        
        logging.info("Sending email to: %s", WP_EMAIL_ADDRESS)
        server.send_message(msg)
        server.quit()
        
        logging.info("✓ Post sent via email successfully!")
        logging.info("✓ WordPress will process it and create a draft post")
        
        return {
            "post_title": title,
            "sent_via": "email",
            "to": WP_EMAIL_ADDRESS,
            "note": "Check WordPress dashboard for the drafted post"
        }
        
    except smtplib.SMTPAuthenticationError:
        error_msg = "Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD in .env"
        logging.error(error_msg)
        raise Exception(error_msg)
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error while sending email: {e}"
        logging.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        logging.error(error_msg)
        raise

def main():
    logging.info("Starting auto-post workflow...")
    
    try:
        topic = choose_topic()
        logging.info("Generated topic: %s", topic)
        
        post = generate_post(topic)
        logging.info("Generated post content")
        
        run_basic_checks(post)
        logging.info("Post passed quality checks")

        # Try XML-RPC publishing first
        try:
            logging.info("Attempting XML-RPC publishing...")
            result = publish_to_wordpress(post, publish_status="draft")
            post_url = result.get("link")
            logging.info("✓ Created draft via XML-RPC: %s", post_url)
        except Exception as xml_rpc_error:
            logging.warning("XML-RPC publishing failed: %s", xml_rpc_error)
            logging.info("Falling back to email-based posting...")
            try:
                result = publish_via_email(post)
                logging.info("✓ Post sent via email (check WordPress dashboard)")
            except Exception as email_error:
                logging.error("Both XML-RPC and email publishing failed!")
                logging.error("XML-RPC error: %s", xml_rpc_error)
                logging.error("Email error: %s", email_error)
                raise
        
        # Log metadata
        with open("publish_log.jsonl", "a") as f:
            logobj = {"topic": topic, "wp_result": result, "ts": int(time.time())}
            f.write(json.dumps(logobj) + "\n")
        
        logging.info("Log saved to publish_log.jsonl")
        
    except Exception as e:
        logging.error("Workflow failed: %s", e)
        logging.error("\nTroubleshooting:")
        logging.error("1. For XML-RPC issues: python3 diagnose_wp.py")
        logging.error("2. For email issues: Check .env has GMAIL_USER, GMAIL_APP_PASSWORD, WP_EMAIL_ADDRESS")
        logging.error("3. Ensure 'Post by Email' is enabled in WordPress Settings")
        raise

if __name__ == "__main__":
    main()
