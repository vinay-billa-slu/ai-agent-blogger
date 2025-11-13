# AI Agent Blogger - Setup & Troubleshooting Guide

## Overview

This script auto-generates blog posts using Google Gemini AI and publishes them to WordPress.

**Features:**
- ✅ Dynamically generates developer-focused topics (no hardcoded list)
- ✅ Generates full blog posts with Gemini AI
- ✅ Publishes to WordPress via XML-RPC (compatible with WordPress.com)
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

Create a `.env` file in the project root:

```properties
GEMINI_API_KEY="your_gemini_api_key_here"
WP_USER="your_wordpress_username"
WORDPRESS_TOKEN="your_wordpress_app_password_or_token"
WP_SITE="https://yourblog.wordpress.com"
```

**Where to get these:**

#### GEMINI_API_KEY
- Go to: https://aistudio.google.com/app/apikeys
- Create a new API key
- Copy the full key

#### WP_USER & WORDPRESS_TOKEN
- For **WordPress.com**: Go to Account Settings → Security → App Passwords
- For **Self-hosted WordPress**: Go to Users → Your Profile → Application Passwords
- Create a new app password (do NOT use your main password)

#### WP_SITE
- For **WordPress.com**: `https://yourblog.wordpress.com`
- For **Self-hosted**: `https://yourdomain.com`

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
export WP_USER="your_user"
export WORDPRESS_TOKEN="your_token"
export WP_SITE="https://your.site"
```

---

### Issue 2: "401 Unauthorized" or "Sorry, you are not allowed to publish posts"

**Cause:** WordPress credentials are invalid or XML-RPC is disabled

**WordPress.com Fixes:**

1. **Check if blog is under correct account:**
   - Log in to WordPress.com with `WP_USER`
   - Go to "My Sites" 
   - Do you see the blog you're trying to publish to?
   - If NOT: The blog is under a different account; use that account's credentials

2. **Enable XML-RPC:**
   - Go to **Settings → Writing**
   - Look for "Remote Publishing" or "XML-RPC"
   - Enable it
   - If you don't see this option, your plan may not support it (upgrade to Business plan)

3. **Check app password format:**
   - WordPress generates passwords with spaces like: `rxn5 s4sc hlpk c7l3`
   - Make sure it's exactly as given (including spaces)
   - Don't mix it with your main password

4. **Test credentials directly:**
   ```python
   import xmlrpc.client, ssl
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ssl_context.verify_mode = ssl.CERT_NONE
   
   server = xmlrpc.client.ServerProxy("https://wordpress.com/xmlrpc.php", context=ssl_context)
   blogs = server.wp.getUsersBlogs("your_user", "your_password")
   print(blogs)  # Should show your blogs
   ```

---

### Issue 3: "404 Not Found" or REST API Errors

**Cause:** REST API is disabled (we now use XML-RPC by default)

**Status:** This is expected. The script now uses XML-RPC which works better with WordPress.com.

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

### Draft vs. Publish

**Default (Draft):** 
```python
result = publish_to_wordpress(post, publish_status="draft")
```
- Post is saved as draft
- You can review before publishing
- No one sees it yet

**Live (Publish):**
```python
result = publish_to_wordpress(post, publish_status="publish")
```
- Post goes live immediately
- Changes this in `main()` function when ready

### Schedule Automated Posts

#### Option 1: cron (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM:
0 9 * * * cd /Users/vinaybilla/Desktop/ai-agent-blogger && python3 auto_post_wp.py
```

#### Option 2: GitHub Actions (Recommended)

Create `.github/workflows/auto-post.yml`:

```yaml
name: Auto Post to WordPress

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
          python-version: '3.11'
      
      - run: pip install -r requirements.txt
      
      - run: python3 auto_post_wp.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          WORDPRESS_TOKEN: ${{ secrets.WORDPRESS_TOKEN }}
          WP_USER: ${{ secrets.WP_USER }}
          WP_SITE: ${{ secrets.WP_SITE }}
```

Then:
1. Add your secrets to GitHub: Settings → Secrets and variables → Actions
2. Commit `.github/workflows/auto-post.yml`
3. Posts will auto-generate daily!

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
A: Yes! Just set `WP_SITE="https://yourdomain.com"` and ensure XML-RPC is enabled in Settings → Writing.

**Q: How do I stop auto-posts?**
A: Delete or comment out the cron job / GitHub workflow, or modify `main()` to not call `publish_to_wordpress()`.

**Q: Can I edit topics before publishing?**
A: Yes! Modify `choose_topic()` to accept user input, or save drafts for manual review.

---

## Support

If you encounter issues:

1. Check the logs: `tail -20 publish_log.jsonl`
2. Run test script to check connectivity
3. Verify all credentials are correct (especially spaces/special chars)
4. Ensure XML-RPC is enabled on your WordPress blog

