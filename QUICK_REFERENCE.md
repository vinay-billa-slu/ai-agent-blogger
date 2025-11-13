# Quick Reference Guide

## One-Liner Commands

### Test & Diagnose
```bash
# Check environment variables are loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓' if os.getenv('GEMINI_API_KEY') else '✗ Missing GEMINI_API_KEY')"

# Send a quick test email to verify SMTP/Post-by-Email
python3 -c "from dotenv import load_dotenv, os; import smtplib; from email.mime.text import MIMEText; load_dotenv(); g=os.getenv('GMAIL_USER'); p=os.getenv('GMAIL_APP_PASSWORD'); w=os.getenv('WP_EMAIL_ADDRESS'); msg=MIMEText('Test body'); msg['Subject']='Test Post'; msg['From']=g; msg['To']=w; s=smtplib.SMTP_SSL('smtp.gmail.com',465); s.login(g,p); s.send_message(msg); s.quit(); print('✓ Test email sent')"
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

### Troubleshooting Quick Map

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing env variables" | .env not found | Verify `.env` and required keys (see Environment Variables below)
| "Couldn't parse JSON" | Gemini format issue | Script falls back to generating plain text post; try re-running
| "Email not creating post" | Wrong WP_EMAIL_ADDRESS or Post-by-Email disabled | Verify WP_EMAIL_ADDRESS in WordPress Settings → Writing

---

## Environment Variables (`.env` format)

```properties
# Required: Google Gemini API
GEMINI_API_KEY="AIza..."

# Required for email publishing
GMAIL_USER="your_gmail@gmail.com"
GMAIL_APP_PASSWORD="your_16_char_app_password"
WP_EMAIL_ADDRESS="publish-abc123@yourblog.wordpress.com"
```

### Getting Credentials

**GEMINI_API_KEY:**
- https://aistudio.google.com/app/apikeys
- Click "Create API Key"
- Copy the key

**WP_USER & WORDPRESS_TOKEN:**
- (No longer used. This project uses Post-by-Email for publishing.)

**WP_SITE:**
- (No longer used. This project uses Post-by-Email for publishing.)

---

## What Each File Does

| File | Purpose |
|------|---------|
| `auto_post_wp.py` | Main script - generates & publishes posts |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (credentials) |
| `publish_log.jsonl` | Log of all published posts |
| `SETUP_AND_TROUBLESHOOTING.md` | Complete setup guide |
| `STATUS.md` | Current status & solutions |

---

## Common Tasks

### Change publish status (draft vs live)
- Post-by-Email behavior is controlled by WordPress settings (not in code)
- Posts are usually created as drafts; publish them manually or configure WordPress to auto-publish

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

**External:**
- 🤖 https://ai.google.dev - Google AI documentation
- 📝 https://developer.wordpress.com/docs/api/ - WordPress API docs

---

## Pro Tips

1. **Test with small posts first** - Review generated content before scheduling large runs
2. **Watch `publish_log.jsonl`** - Verify posts are being created
3. **Keep `.env` secure** - Never commit to git, add to `.gitignore`
4. **Use GitHub Actions** - Much easier than managing cron jobs

---

Last updated: 2025-11-12
