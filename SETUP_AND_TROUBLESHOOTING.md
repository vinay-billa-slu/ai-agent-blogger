# AI Agent Blogger - Setup & Troubleshooting Guide

## Overview

This script auto-generates blog posts using Google Gemini AI and publishes them to WordPress.

**Features:**
- ✅ Dynamically generates developer-focused topics (no hardcoded list)
- ✅ Generates full blog posts with Gemini AI
- ✅ Publishes to WordPress via Post-by-Email (SMTP email delivery)
- ✅ Loads credentials from `.env` file (secure, not in code)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements:**
- `google-genai>=0.12.0` - Google Gemini API SDK
- `requests>=2.28` - HTTP library
- `python-dotenv>=1.0.0` - Load .env files

### 2. Set Up Environment Variables

Create a `.env` file in the project root with the values below. This project now publishes posts using WordPress' "Post-by-Email" feature, so you need a working SMTP account (we document Gmail SMTP below) and the special WordPress posting email address.

```properties
GEMINI_API_KEY="your_gemini_api_key_here"
GMAIL_USER="your_gmail_address@gmail.com"
GMAIL_APP_PASSWORD="your_gmail_app_password"
WP_EMAIL_ADDRESS="your-blog-post-by-email@post.wordpress.com"
```

Where to get these:

#### GEMINI_API_KEY
- Go to: https://aistudio.google.com/app/apikeys
- Create a new API key
- Copy the full key

#### GMAIL_USER & GMAIL_APP_PASSWORD
- For reliable SMTP sending we recommend using an app-specific password (Gmail) rather than your main account password.
- Create an app password in your Google Account (Security → App passwords). Use that value for `GMAIL_APP_PASSWORD`.

If you use another SMTP provider, set `GMAIL_USER`/`GMAIL_APP_PASSWORD` to the appropriate SMTP username and app password. The script defaults to using Gmail's server (smtp.gmail.com:465).

#### WP_EMAIL_ADDRESS (WordPress Post-by-Email address)
- On WordPress.com the Post-by-Email address looks like `something@post.wordpress.com` and can be found in your WordPress dashboard under My Site → Tools → Post by Email (or similar location). Paste that address into `WP_EMAIL_ADDRESS`.
- The Post-by-Email feature typically creates drafts by default; verify the destination mailbox behavior in your WordPress settings.

### 3. Run the Script

```bash
python3 auto_post_wp.py
```

This will:
1. Generate a random developer-focused topic
2. Use Gemini to write a full blog post
3. Publish as a **draft** to WordPress (so you can review)
4. Log the result to `publish_log.jsonl`

---

## Troubleshooting

### Issue 1: "Missing one or more required environment variables"

**Cause:** `.env` file not found or variables not set

**Fix:**
```bash
# Option 1: Create .env file with all variables
echo 'GEMINI_API_KEY="your_key"' > .env

# Option 2: Export as shell variables
export GEMINI_API_KEY="your_key"
export GMAIL_USER="your_gmail_address@gmail.com"
export GMAIL_APP_PASSWORD="your_gmail_app_password"
export WP_EMAIL_ADDRESS="your-blog-post-by-email@post.wordpress.com"
```

---

### Issue 2: Email sending fails or WordPress doesn't receive posts

Common causes and fixes for the email-based publishing flow:

1. SMTP authentication failure (wrong app password)
  - If using Gmail, make sure you created an app-specific password and used that value for `GMAIL_APP_PASSWORD`.
  - If your account has 2FA enabled, the app password is required.

2. SMTP server blocked by network/ISP
  - Some hosting networks restrict outbound SMTP. Test sending from your machine:
    - Use the `test_email()` helper in `auto_post_wp.py` or run the script locally to verify connectivity.

3. Incorrect WordPress Post-by-Email address
  - Double-check `WP_EMAIL_ADDRESS` in your `.env` — it must match the address shown in your WordPress dashboard (looks like `yourcode@post.wordpress.com`).

4. WordPress posted content not showing as expected
  - Post-by-Email behavior depends on WordPress settings — it often creates drafts. Check My Site → Posts or the Drafts section in your WordPress admin.
  - If only the subject appears and no body, ensure the email is sent as a multipart MIME message with an HTML part; `auto_post_wp.py` sends both HTML and plain-text fallback.

---

### Issue 3: REST or REST API-based publishing no longer used

The repository previously attempted to publish via WordPress REST API and other programmatic endpoints. Those approaches were removed because many WordPress.com blogs restrict those endpoints or require upgraded plans.

This project uses Post-by-Email (SMTP) as the reliable publishing method. If you prefer to restore REST API publishing, you can adapt `auto_post_wp.py` to call `/wp-json/wp/v2/posts` with OAuth/Basic auth but be aware many WordPress.com installs do not allow it without a paid plan or elevated permissions.

---

### Issue 4: "SSL: CERTIFICATE_VERIFY_FAILED"

**Cause:** macOS or Linux SSL certificate issues

**Status:** Script now handles this automatically by creating a custom SSL context.

**For Production:** Install proper certificates:
```bash
pip install certifi
# And use: /path/to/certifi/cacert.pem
```

---

### Issue 5: "Couldn't parse JSON from model output"

**Cause:** Gemini returned text that couldn't be parsed as JSON

**Status:** This is expected. The script automatically wraps the content as HTML fallback.

**Result:** Post still publishes successfully, just with less structured formatting.

---

## Publishing Strategy

This project publishes by sending an email to your WordPress Post-by-Email address. Behavior differs slightly from REST/API-based methods:

- Post-by-Email usually creates drafts by default (so you can review before publishing). Check your WordPress settings to confirm.
- If you want posts to publish live automatically, configure WordPress to publish emails automatically (if supported) or manually publish the drafts.

The script sends the post as an HTML multipart email (HTML body + plain-text fallback). Subject becomes post title; body becomes post content (HTML preserved). If you need to change this behavior, edit `publish_via_email()` in `auto_post_wp.py`.

### Schedule Automated Posts

#### Option 1: cron (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM:
0 9 * * * cd /Users/vinaybilla/Desktop/ai-agent-blogger && python3 auto_post_wp.py
```

#### Option 2: GitHub Actions (Recommended)

Create `.github/workflows/auto-post.yml` (or use the provided workflow). Example:

```yaml
name: Auto Post to WordPress (via Email)

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python3 auto_post_wp.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          WP_EMAIL_ADDRESS: ${{ secrets.WP_EMAIL_ADDRESS }}
```

Then:
1. Add your secrets to GitHub: Settings → Secrets and variables → Actions
2. Commit the workflow file
3. The workflow will run on schedule and can also be triggered manually

---

## Monitoring & Logs

### View Recent Posts

```bash
tail -10 publish_log.jsonl
```

Each line contains:
- Topic
- WordPress result (ID, URL)
- Timestamp

### Parse Logs

```python
import json
with open("publish_log.jsonl") as f:
    for line in f:
        log = json.loads(line)
        print(f"Topic: {log['topic']}")
        print(f"Post ID: {log['wp_result'].get('post_id')}")
```

---

## Topic Generation

The script generates developer-focused topics automatically. **No hardcoded list needed!**

**Topics must include keywords from:**
- Languages: Python, Java, Go, Rust, Kotlin, etc.
- AI/ML: Machine Learning, Deep Learning, LLMs, etc.
- Frameworks: Django, FastAPI, Spring, etc.
- DevOps: Kubernetes, Docker, CI/CD, etc.
- Performance: Optimization, Latency, Throughput, etc.
- Other: Testing, Security, Design Patterns, etc.

**If generation fails**, falls back to: `"Developer trends and tooling — YYYY-MM-DD"`

---

## Advanced Configuration

### Use Different Models

Edit `choose_topic()` and `generate_post()` calls:

```python
# Use Gemini 2.0 Pro instead
model="gemini-2.0-pro"
```

Available models: Check https://ai.google.dev/models

### Customize Post Format

Edit `generate_post()` prompt to change:
- Word count (default 700-900)
- Tone (default: "professional, friendly, actionable")
- HTML structure
- Tags format

### Filter Topics

Edit the keyword list in `choose_topic()`:

```python
keywords = [
    "python", "java", "kubernetes",  # Add/remove as needed
    ...
]
```

---

## FAQ

**Q: Will this violate plagiarism policies?**
A: No. Gemini AI generates original content. Always review drafts and add your own insights before publishing.

**Q: Can I use this with Medium, Dev.to, or Hashnode?**
A: Currently only WordPress. Medium/Dev.to have different APIs. PRs welcome!


**Q: Does this work with self-hosted WordPress?**
A: It can. Self-hosted WordPress may not expose a Post-by-Email address by default. Options:

- If your self-hosted host provides an email-to-post address, set `WP_EMAIL_ADDRESS` accordingly and ensure your SMTP account can send to it.
- Alternatively, configure the REST API on your site and provide credentials; note REST requires proper auth (Application Passwords or OAuth) and is outside the default email flow.

**Q: How do I stop auto-posts?**
A: Remove or disable the cron job / GitHub workflow, or modify `main()` to not call `publish_via_email()`.

**Q: Can I edit topics before publishing?**
A: Yes. The script saves post metadata to `publish_log.jsonl` locally and sends drafts to WordPress by default (depending on WP settings). You can modify `choose_topic()` to prompt for input or change `publish_via_email()` to publish live automatically.

---

## Support

If you encounter issues:

1. Check the logs: `tail -20 publish_log.jsonl`
2. Run the `test_email()` helper or `test_content_generation.py` to check connectivity and content generation
3. Verify all credentials are correct (especially spaces/special chars in app passwords)
4. Confirm `WP_EMAIL_ADDRESS` is correct and that WordPress' Post-by-Email is enabled for your site

