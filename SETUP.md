# Setup Guide

Complete setup instructions for the AI Agent Blogger system.

## Prerequisites

- **macOS or Linux** (works on Windows with WSL)
- **Python 3.10+** - Check with `python3 --version`
- **Git** - For cloning and managing the repository
- **Google Account** - For Gemini API access
- **Gmail Account** - For SMTP email sending
- **WordPress Site** - With Post-by-Email feature enabled

## Step 1: Clone the Repository

```bash
git clone https://github.com/vinay-billa-slu/ai-agent-blogger.git
cd ai-agent-blogger
```

## Step 2: Set Up Python Environment

### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed google-genai-0.12.0 python-dotenv-1.0.0 markdown-3.4.1 requests-2.28.0
```

## Step 3: Get Google Gemini API Key

### Create API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click **"Get API key"** button
3. Create a new API key in Google Cloud Console (or use existing project)
4. Copy the API key (keep it secret!)

### Verify API Key Works

```bash
python3 << 'EOF'
from google import genai
import os

api_key = "your-api-key-here"  # Replace with actual key
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello"
)
print("✓ Gemini API works:", response.text)
EOF
```

## Step 4: Set Up Gmail SMTP

### Create App Password

Gmail requires an app-specific password for SMTP (not your regular password):

1. Go to [Google Account](https://myaccount.google.com/)
2. Navigate to **Security** (left sidebar)
3. Scroll down to **App passwords** (requires 2FA enabled)
4. Select **Mail** and **Windows Computer** (or your device type)
5. Click **Generate**
6. Copy the 16-character password (remove spaces)

**Example:** `abcd efgh ijkl mnop` → `abcdefghijklmnop`

### Verify Gmail SMTP Connection

```bash
python3 << 'EOF'
import smtplib

gmail_user = "your-email@gmail.com"  # Replace
gmail_pass = "your-app-password"      # Replace (16 chars)

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
    server.login(gmail_user, gmail_pass)
    server.quit()
    print("✓ Gmail SMTP connection works")
except Exception as e:
    print("✗ Gmail SMTP failed:", e)
EOF
```

## Step 5: Configure WordPress Post-by-Email

### Enable Post-by-Email

1. Log in to WordPress Admin
2. Go to **Settings** → **Post-by-Email**
3. Generate a new email address for publishing
4. **Copy this email address** - you'll need it in `.env`

### Example

```
Mail Server: mail.example.com (or provided by WordPress host)
Published Category: Blog (or your preferred default)
Post Status: Draft (recommended - review before publishing)
```

### Test Email Address

The Post-by-Email email typically looks like:
```
publish-12345@example.wordpress.com
```

### Verify Connection

Send a test email from Gmail to your WordPress Post-by-Email address:

1. Open Gmail
2. Compose new email
3. To: `publish-xxxx@example.wordpress.com`
4. Subject: `Test Post`
5. Body: `This is a test post with **bold** text`
6. Send
7. Check WordPress Admin → Posts → All Posts for a new Draft

## Step 6: Create `.env` File

Create a `.env` file in the project root with your secrets:

```bash
cat > .env << 'EOF'
# Google Gemini API
GEMINI_API_KEY=your-api-key-here

# Gmail SMTP (for sending emails)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# WordPress Post-by-Email
WP_EMAIL_ADDRESS=publish-xxxxx@example.wordpress.com
EOF
```

### Security

⚠️ **Important:** Never commit `.env` to Git. It's already in `.gitignore`.

```bash
# Verify .env is not tracked
git status | grep .env  # Should show nothing
```

## Step 7: Verify Configuration

Test that all configuration is working:

```bash
python3 auto_post_wp.py --dry-run
```

**Expected output:**
```
2025-11-19 14:30:00 INFO Starting auto-post flow
2025-11-19 14:30:00 INFO Category rotation: Programming Languages (index 1/10)
2025-11-19 14:30:03 INFO ✓ Generated topic (Category: Programming Languages): Understanding Python Decorators
2025-11-19 14:30:03 INFO Generated post
2025-11-19 14:30:15 INFO Preparing to send email via Gmail SMTP to publish-xxxx@example.com
2025-11-19 14:30:15 INFO Subject: Understanding Python Decorators
2025-11-19 14:30:15 INFO Dry run enabled — not sending. Message preview above.
```

### Common Setup Issues

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY` not found | Check `.env` file exists and contains the key |
| `GMAIL_USER` not found | Check Gmail email is in `.env` |
| `GMAIL_APP_PASSWORD` not found | Check app password is in `.env` (16 chars, no spaces) |
| `WP_EMAIL_ADDRESS` not found | Check WordPress Post-by-Email address is in `.env` |
| Gmail SMTP connection failed | Verify app password (not regular password); enable 2FA |
| Gemini API returns error | Verify API key is valid; check quota in Google Cloud Console |

## Step 8: Send a Test Email

Once verified with `--dry-run`, send a real test email:

```bash
python3 auto_post_wp.py
```

**What happens:**
1. Generates a topic
2. Generates a blog post
3. Sends email to WordPress Post-by-Email
4. Records result in `publish_log.jsonl`

**Verify in WordPress:**
1. Log in to WordPress Admin
2. Go to **Posts** → **All Posts**
3. Look for a new **Draft** post with the generated title
4. Review the formatting and content
5. Publish manually or schedule

## Step 9: Set Up GitHub Actions (Optional)

For automated daily publishing:

1. **Fork or own the repository** on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:
   - `GEMINI_API_KEY` - Your Gemini API key
   - `GMAIL_USER` - Your Gmail email
   - `GMAIL_APP_PASSWORD` - Your Gmail app password
   - `WP_EMAIL_ADDRESS` - Your WordPress Post-by-Email address

4. Verify workflow is enabled:
   - Go to **Actions** tab
   - "Publish Blog Post" workflow should be visible

5. Test manually:
   - Click **Publish Blog Post** workflow
   - Click **Run workflow** button
   - Check workflow logs after it completes

### Schedule Configuration

The workflow runs automatically **daily at 09:00 UTC**. To change:

1. Edit `.github/workflows/schedule_publish.yml`
2. Modify the `cron` schedule:

```yaml
schedule:
  - cron: '0 9 * * *'  # 09:00 UTC daily
```

**Common cron patterns:**
- `0 9 * * *` - Daily at 09:00 UTC
- `0 9 * * 1` - Weekly on Monday at 09:00 UTC
- `0 */6 * * *` - Every 6 hours
- `0 12 * * 1,3,5` - Monday/Wednesday/Friday at 12:00 UTC

## Step 10: Production Checklist

Before deploying to production:

- [ ] `.env` file created locally with all secrets
- [ ] `--dry-run` test successful
- [ ] Test email sent and appears in WordPress as Draft
- [ ] Post formatting looks correct (headings, code blocks, bold/italic)
- [ ] GitHub secrets configured (if using Actions)
- [ ] GitHub Actions test run successful
- [ ] Topic tracker initialized: `cat topic_tracker.json`
- [ ] Publish log exists: `ls -la publish_log.jsonl`

## Directory Structure

After setup, your project should have:

```
ai-agent-blogger/
├── auto_post_wp.py              # Main script
├── requirements.txt              # Python dependencies
├── .env                          # Secrets (not in git)
├── .gitignore                    # Excludes .env and cache
├── .github/
│   └── workflows/
│       └── schedule_publish.yml  # GitHub Actions workflow
├── topic_tracker.json            # Generated: topic history
├── publish_log.jsonl             # Generated: publication log
├── README.md                     # Project documentation
├── SETUP.md                      # This file
├── TESTING_GUIDE.md              # Testing instructions
├── CONTENT_GENERATION.md         # Content customization
└── TROUBLESHOOTING.md            # Debugging guide
```

## Troubleshooting Setup

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging.

### Quick Checks

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "google-genai|python-dotenv|markdown"

# Check .env exists
ls -la .env

# Check API key works
python3 auto_post_wp.py --dry-run

# Check Gmail works
python3 auto_post_wp.py --dry-run --show
```

## Next Steps

1. Read [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing strategies
2. Read [CONTENT_GENERATION.md](CONTENT_GENERATION.md) for customization
3. See [README.md](README.md) for architecture and features
4. Visit [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if issues arise
