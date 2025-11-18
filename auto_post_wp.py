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
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from markdown import markdown

# --- Google GenAI (Gemini) client
from google import genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

try:
    load_dotenv()
except Exception:
    logging.debug("No .env loaded; relying on environment variables")

GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
WP_EMAIL_ADDRESS = os.getenv("WP_EMAIL_ADDRESS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "paxep16902@agenra.com")  # SendGrid verified sender

if not GENAI_API_KEY:
    logging.error("Missing GEMINI_API_KEY")
    raise SystemExit(1)

# if not SENDGRID_API_KEY:
#     logging.error("Missing SENDGRID_API_KEY")
#     raise SystemExit(1)

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


def _looks_truncated(text: str) -> bool:
    """Rudimentary check whether the model output appears truncated.

    Returns True if the text ends abruptly (no terminal punctuation) or
    ends with an incomplete code fence marker. This is a heuristic only.
    """
    if not text:
        return True
    text = text.rstrip()
    # If ends with common sentence terminators, assume complete
    if text.endswith((".", "?", "!", '"', "'")):
        return False
    # If ends with a code fence start or backticks, consider truncated
    if text.endswith("```)" ) or text.endswith("```"):
        return True
    # Otherwise, if last line is very short (single word), suspect truncation
    last_line = text.splitlines()[-1]
    if len(last_line.split()) <= 4 and not last_line.endswith(('.', '?', '!')):
        return True
    return False


def _replace_placeholder_tokens_with_fences(text: str) -> str:
    """Replace literal CODEBLOCK_N tokens with fenced bash code blocks.
    
    This is a fallback when the model generates placeholders instead of real code.
    """
    def replacer(m):
        token = m.group(0)
        # Replace each placeholder with a fenced bash block containing the token itself
        # This at least prevents the literal CODEBLOCK_N from appearing in the final output
        return f"```bash\n# {token} — code example would appear here\n```"
    
    return re.sub(r'\bCODEBLOCK_\d+\b', replacer, text)


def generate_post(topic, model="gemini-2.0-flash", max_output_tokens=3000, max_continue_attempts=3):
    prompt = f"""Write a 500-1000 word blog post about: {topic}

AUDIENCE & TONE:
- Write for software developers and engineers
- Use an engaging, conversational tone
- Explain complex topics in an understandable way
- Include practical examples

FORMATTING FOR WORDPRESS POST-BY-EMAIL (CRITICAL):
The output will be sent as plain text email to WordPress. Use this EXACT markdown format:

Section Headers: Use # for main sections (will be converted to bold)
Example:
# Why This Matters

Emphasis: Use *text* for italics (single asterisks) and **text** for bold
Example: This is *important* and this is **bold** using asterisks

Code Blocks: ALWAYS use triple backticks with language name
```bash
echo "example bash command"
```

```yaml
apiVersion: v1
kind: Pod
```

```python
def example():
    print("python code")
```

Bullet Points: Use * at start of line
* First item
* Second item

Paragraphs: Separate with blank lines (double newline)

CONTENT REQUIREMENTS:
- Start directly with content (skip introductions)
- Include 3-5 real, working code examples with proper syntax
- Each code block MUST have correct language identifier (bash, yaml, python, javascript, etc)
- Each code example must be complete and functional
- Use inline backticks for code references: `kubectl`, `variable_name`, etc.

ABSOLUTELY FORBIDDEN:
- NO HTML tags at all (<p>, <strong>, <h1>, etc.)
- NO placeholder text like "code example here"
- NO CODEBLOCK_0, CODEBLOCK_1 tokens
- NO empty code blocks

REQUIRED OUTPUT:
- Plain text only
- Proper markdown with # headings, * bullets, ``` code blocks
- Minimum 3-4 real code examples
- Every code block has language name
- Double line breaks between major sections"""
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    text = getattr(response, "text", None) or str(response)
    text = text.strip()

    # Remove any HTML tags that might have been added despite instructions
    text = re.sub(r'<[^>]+>', '', text)

    # Remove any code fence artifacts at the start/end
    if text.startswith("```"):
        text = re.sub(r'^```.*?\n', '', text)
    if text.endswith("```"):
        text = re.sub(r'\n```$', '', text)

    # Check for literal CODEBLOCK_N placeholders (indicates model failed to generate code)
    placeholder_pattern = r'\bCODEBLOCK_\d+\b'
    has_placeholders = re.search(placeholder_pattern, text)
    logging.info(f"Initial generation check: placeholders found = {bool(has_placeholders)}")
    if has_placeholders:
        logging.info(f"Placeholder matches: {re.findall(placeholder_pattern, text)}")
    
    placeholder_count = 0
    max_placeholder_attempts = 3
    while re.search(placeholder_pattern, text) and placeholder_count < max_placeholder_attempts:
        placeholder_count += 1
        logging.info(
            f"[REGEN ATTEMPT {placeholder_count}/{max_placeholder_attempts}] "
            f"Model generated literal CODEBLOCK_N placeholders instead of real code. "
            f"Requesting full regeneration."
        )
        # Request a complete regeneration with explicit instruction to include code
        regen_prompt = (
            f"Rewrite the blog post about '{topic}'. "
            f"CRITICAL: Do NOT write CODEBLOCK_0, CODEBLOCK_1, etc. placeholders. "
            f"Instead, write the actual example code inline. "
            f"Every code example must have the format: three backticks + language + code + three backticks "
            f"Example: ```bash\\necho hello\\n``` or ```python\\nprint('hi')\\n``` "
            f"Output plain text. NO placeholders. REAL CODE ONLY."
        )
        try:
            regen_resp = client.models.generate_content(
                model=model,
                contents=regen_prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=max_output_tokens),
            )
            regen_text = getattr(regen_resp, "text", None) or str(regen_resp)
            regen_text = regen_text.strip()
            
            # Check if regeneration produced code or still has placeholders
            has_regen_placeholders = re.search(placeholder_pattern, regen_text)
            logging.info(f"[REGEN {placeholder_count}] Result: placeholders_in_response = {bool(has_regen_placeholders)}")
            
            if not has_regen_placeholders:
                logging.info(f"✓ Regeneration {placeholder_count} succeeded - no placeholders detected")
                text = regen_text
                break
            else:
                found_placeholders = re.findall(placeholder_pattern, regen_text)
                logging.warning(f"[REGEN {placeholder_count}] Still has placeholders: {found_placeholders[:5]}")
        except Exception as e:
            logging.exception(f"[REGEN {placeholder_count}] Call failed: {e}")
            break
    
    # If we still have placeholders after retries, use the fallback wrapper
    final_check = re.search(placeholder_pattern, text)
    if final_check:
        found_placeholders = re.findall(placeholder_pattern, text)
        logging.warning(f"After all regeneration attempts, still have placeholders: {found_placeholders[:5]}. Using fallback wrapping.")
        text = _replace_placeholder_tokens_with_fences(text)
    else:
        logging.info("✓ No placeholders in final output - proceeding to conversion")

    # If the output looks truncated, attempt to continue the generation
    attempts = 0
    while attempts < max_continue_attempts and _looks_truncated(text):
        attempts += 1
        logging.info("Output looks truncated; attempting continuation (attempt %d)", attempts)
        cont_prompt = (
            "Continue the previous blog post from where it left off. "
            "Do NOT repeat what was already written. Output plain text only."
        )
        try:
            cont_resp = client.models.generate_content(
                model=model,
                contents=cont_prompt,
                config=genai.types.GenerateContentConfig(max_output_tokens=800),
            )
            cont_text = getattr(cont_resp, "text", None) or str(cont_resp)
            cont_text = cont_text.strip()
            # Clean continuation
            cont_text = re.sub(r'<[^>]+>', '', cont_text)
            if cont_text.startswith("```"):
                cont_text = re.sub(r'^```.*?\n', '', cont_text)
            if cont_text.endswith("```"):
                cont_text = re.sub(r'\n```$', '', cont_text)
            # Append with a separating newline
            if cont_text:
                text = text + "\n\n" + cont_text
        except Exception:
            logging.exception("Continuation attempt failed")
            break

    return {
        "title": topic,
        "body_html": text,  # Plain text, kept as body_html for compatibility with publish_via_email
        "tags": [t.lower() for t in topic.split()[:4]]
    }


def run_basic_checks(post):
    """Validate required environment for Gmail transport (only transport supported)."""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    if not (gmail_user and gmail_pass and WP_EMAIL_ADDRESS):
        raise ValueError("GMAIL_USER, GMAIL_APP_PASSWORD and WP_EMAIL_ADDRESS are required in environment for Gmail transport")
    return True


def _convert_markdown_to_plain_and_html(markdown_text: str):
    """Convert markdown text to HTML for WordPress Post-by-Email rendering.
    
    WordPress Post-by-Email recognizes HTML and will render:
    - <h4>, <h5> tags as headings
    - <strong> and <em> for bold and italic
    - <pre><code> for code blocks with styling
    - <ul><li> for bullet points
    - Proper line breaks
    
    This function converts markdown to HTML so WordPress receives
    professionally formatted content.
    """
    lines = markdown_text.split('\n')
    html_lines = []
    in_code_block = False
    current_code_lang = ''
    current_code_content = []
    in_list = False
    
    for line in lines:
        # Handle code blocks
        if line.strip().startswith('```'):
            if not in_code_block:
                # Starting a code block
                in_code_block = True
                current_code_lang = line.strip()[3:].strip() or 'text'
                current_code_content = []
                continue
            else:
                # Ending a code block
                in_code_block = False
                code_text = '\n'.join(current_code_content)
                # Escape HTML
                code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Create styled code block
                html_code = (
                    f'<div style="background: #f5f5f5; border: 1px solid #ddd; border-left: 4px solid #0073aa; '
                    f'padding: 12px 15px; margin: 15px 0; border-radius: 3px; overflow-x: auto;">'
                    f'<div style="color: #666; font-size: 12px; margin-bottom: 8px; font-weight: bold;">'
                    f'{current_code_lang}</div>'
                    f'<pre style="margin: 0; font-family: monospace; font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word;">'
                    f'<code>{code_text}</code></pre></div>'
                )
                html_lines.append(html_code)
                current_code_content = []
                continue
        
        if in_code_block:
            current_code_content.append(line)
            continue
        
        line = line.rstrip()
        
        # Skip empty lines outside of lists
        if not line.strip():
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            elif html_lines and not html_lines[-1].endswith('</p>'):
                html_lines.append('<br/>')
            continue
        
        # Handle headings: # -> <h2>, ## -> <h3>, ### -> <h3>
        if line.startswith('#'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            
            heading_text = re.sub(r'^#+\s*', '', line).strip()
            # Convert markdown formatting in heading
            heading_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', heading_text)
            heading_text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', heading_text)
            heading_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', heading_text)
            
            html_lines.append(f'<h5 style="margin: 20px 0 10px 0; color: #222; font-weight: 600; border-bottom: 2px solid #0073aa; padding-bottom: 8px;">{heading_text}</h5>')
            continue
        
        # Handle bullet points
        if line.strip().startswith('*') and not '**' in line:
            item_text = re.sub(r'^\*\s*', '', line).strip()
            # Convert markdown formatting
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', item_text)
            item_text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', item_text)
            item_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', item_text)
            
            if not in_list:
                html_lines.append('<ul style="margin: 10px 0; padding-left: 30px;">')
                in_list = True
            html_lines.append(f'<li style="margin: 5px 0;">{item_text}</li>')
            continue
        
        # Regular paragraph
        if in_list:
            html_lines.append('</ul>')
            in_list = False
        
        # Convert markdown formatting to HTML
        para_text = line
        # Bold
        para_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', para_text)
        # Italic
        para_text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', para_text)
        # Inline code
        para_text = re.sub(r'`([^`]+)`', r'<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px; font-family: monospace;">\1</code>', para_text)
        
        html_lines.append(f'<p style="margin: 10px 0; line-height: 1.6; color: #333;">{para_text}</p>')
    
    # Close any open list
    if in_list:
        html_lines.append('</ul>')
    
    # Build full HTML document
    html_body = '\n'.join(html_lines)
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h2, h3, h4, h5, h6 {{
            color: #222;
            font-weight: 600;
        }}
        code {{
            font-family: 'Courier New', monospace;
        }}
        pre {{
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    return html_body, full_html








def publish_via_rest_api(post, dry_run=False, show=False, save=False):
    """Publish directly to WordPress via REST API (bypasses Post-by-Email).
    
    Requires WP_SITE, WP_USER, and WP_APP_PASSWORD in environment.
    WP_APP_PASSWORD is a WordPress Application Password (created in WordPress admin).
    """
    import base64
    try:
        import requests
    except ImportError:
        logging.error("requests library required for REST API publishing. Install with: pip install requests")
        raise SystemExit(1)
    
    wp_site = os.getenv("WP_SITE")
    wp_user = os.getenv("WP_USER")
    wp_app_password = os.getenv("WP_APP_PASSWORD")
    
    if not (wp_site and wp_user and wp_app_password):
        raise ValueError(
            "WP_SITE, WP_USER, and WP_APP_PASSWORD are required in environment for REST API transport. "
            "WP_APP_PASSWORD can be created in WordPress: Settings → Users → Your Profile → Application Passwords"
        )
    
    title = post.get("title", "Untitled")
    body_html = post.get("body_html", "")
    body_plain = re.sub(r'<[^>]+>', '', body_html).strip()
    
    # Convert to plain with shortcodes and HTML
    plain_with_shortcodes, html_body = _convert_markdown_to_plain_and_html(body_plain)
    
    # The HTML body (extract just the <body> content for the post)
    body_match = re.search(r'<body>(.*?)</body>', html_body, re.DOTALL)
    post_content = body_match.group(1).strip() if body_match else html_body
    
    # Prepare REST API request
    wp_rest_url = f"{wp_site.rstrip('/')}/wp-json/wp/v2/posts"
    auth_header = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    post_data = {
        "title": title,
        "content": post_content,
        "status": "draft",  # Create as draft; user can publish manually
        "excerpt": post_content[:200]  # First 200 chars as excerpt
    }
    
    logging.info("Preparing to post via WordPress REST API to %s", wp_rest_url)
    logging.info("Subject: %s", title)
    logging.info("Content length: %d chars", len(post_content))
    logging.info("Status: draft (you'll publish manually)")
    
    if show:
        print("\n----- REST API POST DATA -----\n")
        print(f"Title: {title}\n")
        print("Content (HTML):")
        print(post_content)
        print("\n----- END -----\n")
    
    if save:
        fname = f"last_post_{int(time.time())}.txt"
        try:
            with open(fname, "w", encoding="utf-8") as fh:
                fh.write(f"Title: {title}\n\n")
                fh.write(f"REST API POST DATA:\n\n")
                fh.write(post_content)
            logging.info("Saved full post to %s", fname)
        except Exception:
            logging.exception("Failed to save post to file")
    
    if dry_run:
        logging.info("Dry run enabled — not posting. Preview saved above.")
        return {"post_title": title, "wp_site": wp_site, "dry_run": True, "transport": "rest"}
    
    try:
        response = requests.post(wp_rest_url, json=post_data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        post_id = result.get("id")
        post_link = result.get("link")
        logging.info("✓ Post created successfully via REST API: %s", post_link)
        return {
            "post_title": title,
            "post_id": post_id,
            "post_link": post_link,
            "wp_site": wp_site,
            "transport": "rest"
        }
    except Exception as e:
        logging.error("Error posting via REST API: %s", e)
        raise


def publish_via_gmail(post, dry_run=False, show=False, save=False):
    """Send the post via Gmail SMTP to the WP email address as HTML.
    
    Formats the markdown content to beautiful HTML that WordPress Post-by-Email
    will render with proper styling, headings, bold, italics, and code blocks.
    
    Requires GMAIL_USER and GMAIL_APP_PASSWORD in environment (app password).
    """
    run_basic_checks(post)
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    to_addr = WP_EMAIL_ADDRESS

    title = post.get("title", "Untitled")
    body_text = post.get("body_html", "")  # body_html is actually raw text now
    
    # Convert markdown to HTML
    _, html_body = _convert_markdown_to_plain_and_html(body_text)
    
    # Extract just the body content from the HTML
    body_match = re.search(r'<body>(.*?)</body>', html_body, re.DOTALL)
    html_content = body_match.group(1).strip() if body_match else html_body
    
    # Add title as h4 at the top
    email_html = f'<h4 style="color: #222; font-size: 28px; margin: 0 0 20px 0;">{title}</h4>\n{html_content}'

    # Build MIME message as HTML
    msg = MIMEText(email_html, 'html', _charset='utf-8')
    msg['Subject'] = title
    msg['From'] = gmail_user
    msg['To'] = to_addr

    logging.info("Preparing to send email via Gmail SMTP to %s", to_addr)
    logging.info("Subject: %s", title)
    logging.info("Body length (HTML): %d chars", len(email_html))
    logging.info("Message type: HTML (proper formatting for WordPress Post-by-Email)")

    # DEBUG: Log first 500 chars of content being sent
    logging.info("HTML CONTENT (first 500 chars):\n%s", email_html[:500])

    # Optionally show or save the full post for inspection/debugging
    if show:
        print("\n----- GENERATED POST FOR WORDPRESS (HTML) -----\n")
        print(email_html)
        print("\n----- END -----\n")

    if save:
        fname = f"last_post_{int(time.time())}.txt"
        try:
            with open(fname, "w", encoding="utf-8") as fh:
                fh.write(f"Subject: {title}\n\n")
                fh.write(f"HTML EMAIL BODY (proper formatting):\n\n")
                fh.write(email_html)
            logging.info("Saved full post to %s", fname)
        except Exception:
            logging.exception("Failed to save post to file")

    if dry_run:
        logging.info("Dry run enabled — not sending. Message preview above.")
        return {"post_title": title, "to": to_addr, "dry_run": True}

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, [to_addr], msg.as_string())
        server.quit()
        logging.info("✓ Email sent successfully via Gmail SMTP (HTML with proper formatting)")
        return {"post_title": title, "to": to_addr}
    except Exception as e:
        logging.error("Error sending email via Gmail: %s", e)
        raise



def main():
    parser = argparse.ArgumentParser(description="Auto post to WordPress via email (Gmail only) or REST API")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send email; print payload instead.")
    parser.add_argument("--show", action="store_true", help="Print the full generated post to the console before sending")
    parser.add_argument("--save", action="store_true", help="Save the full generated post to a file before sending")
    parser.add_argument("--transport", choices=["gmail", "rest"], default="gmail", help="Transport method: 'gmail' (Post-by-Email) or 'rest' (WordPress REST API)")
    args = parser.parse_args()

    logging.info("Starting auto-post flow")
    topic = choose_topic()
    logging.info("Topic: %s", topic)
    post = generate_post(topic)
    logging.info("Generated post")

    # Route to appropriate transport
    if args.transport == "rest":
        result = publish_via_rest_api(post, dry_run=args.dry_run, show=args.show, save=args.save)
    else:
        result = publish_via_gmail(post, dry_run=args.dry_run, show=args.show, save=args.save)

    with open("publish_log.jsonl", "a") as f:
        f.write(json.dumps({"topic": topic, "result": result, "ts": int(time.time()), "transport": args.transport}) + "\n")
    logging.info("Done. Result: %s", result)


if __name__ == "__main__":
    main()
