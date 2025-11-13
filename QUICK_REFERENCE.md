# Quick Reference Guide

## One-Liner Commands

### Test & Diagnose
```bash
# Full diagnostic (ALWAYS run this first!)
python3 diagnose_wp.py

# Check environment variables are loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓' if os.getenv('GEMINI_API_KEY') else '✗ Missing GEMINI_API_KEY')"

# Test WordPress credentials
python3 << 'EOF'
import xmlrpc.client, ssl, os
from dotenv import load_dotenv
load_dotenv()
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = ssl_ctx.verify_mode = False
server = xmlrpc.client.ServerProxy("https://wordpress.com/xmlrpc.php", context=ssl_ctx)
print("✓ Authenticated" if server.wp.getUsersBlogs(os.getenv('WP_USER'), os.getenv('WORDPRESS_TOKEN')) else "✗ Auth failed")
EOF
```

### Run the Script
```bash
# Generate & publish one blog post as draft
python3 auto_post_wp.py

# Run daily at 9 AM (macOS/Linux cron)
crontab -e
# Add: 0 9 * * * cd /path/to/project && python3 auto_post_wp.py
```

### Logs & Monitoring
```bash
# See latest posts generated
tail -10 publish_log.jsonl

# Watch posts being generated (real-time)
tail -f publish_log.jsonl

# Pretty-print logs
python3 -c "import json; [print(json.dumps(json.loads(line), indent=2)) for line in open('publish_log.jsonl')]"
```

### Install/Update Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Or install one by one
pip install google-genai requests python-dotenv
```

---

## Troubleshooting Quick Map

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing env variables" | .env not found | Run `python3 diagnose_wp.py` |
| "401 Unauthorized" | Wrong credentials | Check blog owner, run `diagnose_wp.py` |
| "0 blogs found" | Wrong account | Update WP_USER in .env |
| "Certificate verify failed" | SSL issue | Already handled by script |
| "Couldn't parse JSON" | Gemini format issue | Expected, posts still publish |
| "404 Not Found" | REST API disabled | Script uses XML-RPC now (should work) |

---

## Environment Variables (`.env` format)

```properties
# Required: Google Gemini API
GEMINI_API_KEY="AIza..."

# Required: WordPress credentials
WP_USER="your_blog_username"
WORDPRESS_TOKEN="your_app_password"
WP_SITE="https://your.blog.com"
```

### Getting Credentials

**GEMINI_API_KEY:**
- https://aistudio.google.com/app/apikeys
- Click "Create API Key"
- Copy the key

**WP_USER & WORDPRESS_TOKEN:**
- Log into WordPress.com dashboard
- Settings → Security → App Passwords
- Create new app password
- Copy username & password

**WP_SITE:**
- WordPress.com: `https://yourblog.wordpress.com`
- Self-hosted: `https://yourdomain.com`

---

## What Each File Does

| File | Purpose |
|------|---------|
| `auto_post_wp.py` | Main script - generates & publishes posts |
| `diagnose_wp.py` | Diagnostic tool - tests WordPress connection |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (credentials) |
| `publish_log.jsonl` | Log of all published posts |
| `SETUP_AND_TROUBLESHOOTING.md` | Complete setup guide |
| `STATUS.md` | Current status & solutions |

---

## Common Tasks

### Change publish status (draft vs live)
Edit `auto_post_wp.py` line ~190:
```python
# Change from:
result = publish_to_wordpress(post, publish_status="draft")
# To:
result = publish_to_wordpress(post, publish_status="publish")
```

### Change Gemini model
Edit `choose_topic()` and `generate_post()` functions:
```python
model="gemini-2.0-pro"  # Change this
```
See: https://ai.google.dev/models

### Change topic constraints
Edit `choose_topic()` function, keywords list (~line 60):
```python
keywords = [
    "python", "kubernetes", "docker",  # Add/remove topics
    ...
]
```

### Schedule on GitHub Actions
Create `.github/workflows/auto-post.yml` (see `SETUP_AND_TROUBLESHOOTING.md`)

---

## Support Resources

**This project:**
- 📖 `SETUP_AND_TROUBLESHOOTING.md` - Complete guide
- 📊 `STATUS.md` - Current issues & solutions
- 🔧 `diagnose_wp.py` - Interactive troubleshooting

**External:**
- 🤖 https://ai.google.dev - Google AI documentation
- 📝 https://developer.wordpress.com/docs/api/ - WordPress API docs
- 🐍 https://docs.python.org/3/library/xmlrpc.html - XML-RPC library docs

---

## Pro Tips

1. **Always run `diagnose_wp.py` first** - Saves hours of debugging
2. **Test with `publish_status="draft"` first** - Review before going live
3. **Watch `publish_log.jsonl`** - Verify posts are being created
4. **Keep `.env` secure** - Never commit to git, add to `.gitignore`
5. **Use GitHub Actions** - Much easier than managing cron jobs

---

Last updated: 2025-11-12
