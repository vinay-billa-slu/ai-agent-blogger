# Email-Based Posting Setup Guide

## Overview

WordPress has deprecated/restricted XML-RPC and REST API access on many shared hosting environments. The recommended workaround is **Post by Email** — a built-in WordPress feature that creates posts by receiving emails at a special address.

**How it works:**
1. WordPress creates a special email address (e.g., `publish-abc123@yourblog.wordpress.com`)
2. You send posts to that address using Gmail SMTP
3. WordPress automatically creates draft posts from received emails
4. You can review and publish them manually

---

## Setup Instructions

### Step 1: Enable Post by Email in WordPress

1. Log into your WordPress dashboard: `https://vinaybilla5.wordpress.com/wp-admin`
2. Go to **Settings → Writing**
3. Scroll down to **Post by Email**
4. Look for: **"Post by Email address"** (something like: `publish-abc123@vinaybilla5.wordpress.com`)
5. **Copy this address** — you'll need it next

If you don't see "Post by Email":
- It may be disabled by your hosting provider
- Try going to **Settings → General** and check if there are any email settings
- Contact your hosting support to enable it

---

### Step 2: Configure Gmail App Password

WordPress Post by Email requires Gmail SMTP authentication. You need an **app-specific password** (NOT your main Gmail password).

**Steps to create Gmail app password:**

1. Go to: https://myaccount.google.com/security
2. On the left sidebar, click **Security**
3. Under "How you sign in to Google", enable **Two-Factor Authentication** (if not already enabled)
4. After enabling 2FA, go back to **Security**
5. Look for **App passwords** (appears only after 2FA is enabled)
6. Select:
   - App: **Mail**
   - Device: **Windows Computer** (or your device type)
7. Click **Generate**
8. Google will show a 16-character app password (with spaces like: `qdag yafo nlzq pxbc`)
9. **Copy this password**

---

### Step 3: Update `.env` File

Edit `/Users/vinaybilla/Desktop/ai-agent-blogger/.env` and add:

```properties
# Gmail credentials for Post by Email
GMAIL_USER="your_gmail@gmail.com"
GMAIL_APP_PASSWORD="qdag yafo nlzq pxbc"
WP_EMAIL_ADDRESS="publish-abc123@vinaybilla5.wordpress.com"
```

**Replace with your actual values:**
- `GMAIL_USER`: Your Gmail address (must be @gmail.com)
- `GMAIL_APP_PASSWORD`: The 16-char app password from Step 2 (keep the spaces)
- `WP_EMAIL_ADDRESS`: The Post by Email address from Step 1

### Example:
```properties
GEMINI_API_KEY="AIzaSyBNC6pBQ__X324Q-jJ7_6dHhjXXS2H7_MQ"
WP_USER="vinaybilla2021"
WORDPRESS_TOKEN='rxn5 s4sc hlpk c7l3'
WP_SITE="https://vinaybilla5.wordpress.com"

# Email-based posting (Post by Email feature)
GMAIL_USER="myname@gmail.com"
GMAIL_APP_PASSWORD="qdag yafo nlzq pxbc"
WP_EMAIL_ADDRESS="publish-abc123@vinaybilla5.wordpress.com"
```

---

### Step 4: Test the Configuration

Run the setup helper (optional, but recommended):
```bash
python3 setup_email_posting.py
```

This script will:
- Verify your WordPress Post by Email address
- Test Gmail SMTP connection
- Update .env automatically

---

## Usage

Once configured, the script will automatically:

1. **Try XML-RPC first** (if available)
2. **Fall back to email** if XML-RPC fails

### Run the script:
```bash
python3 auto_post_wp.py
```

Expected output:
```
INFO Attempting XML-RPC publishing...
WARNING XML-RPC publishing failed: [error details]
INFO Falling back to email-based posting...
INFO ✓ Post sent via email (check WordPress dashboard)
```

### Check for drafted posts:
- Log into WordPress dashboard
- Go to **Posts → Drafts**
- You should see a new draft with the generated content
- Review and publish manually, or configure as needed

---

## Troubleshooting

### Error: "Gmail authentication failed"

**Causes:**
- Wrong Gmail address or app password
- Gmail app password not set up correctly
- 2FA not enabled

**Fix:**
1. Verify you're using a Gmail address (ending in @gmail.com)
2. Check that the app password is exactly as shown (with spaces)
3. Ensure Two-Factor Authentication is enabled: https://myaccount.google.com/security
4. Generate a new app password if needed
5. Update `.env` and try again

### Error: "Post by Email address not set"

**Causes:**
- WP_EMAIL_ADDRESS missing or wrong in `.env`
- Post by Email not enabled in WordPress

**Fix:**
1. Double-check the address in WordPress Settings → Writing
2. Make sure it's in `.env` as `WP_EMAIL_ADDRESS`
3. Ask hosting support if Post by Email is disabled

### Emails sent but no posts appear in WordPress

**Causes:**
- Email address wrong or typo
- WordPress Post by Email filters email as spam
- Email not actually sending

**Fix:**
1. Check WordPress dashboard for spam/deleted emails
2. Go to **Posts → Trash** and check if posts were moved there
3. Send a test email manually to verify the address works
4. Check WordPress logs if available (ask hosting provider)

### How to manually test email sending

```bash
python3 << 'EOF'
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()
gmail = os.getenv("GMAIL_USER")
password = os.getenv("GMAIL_APP_PASSWORD")
wp_email = os.getenv("WP_EMAIL_ADDRESS")

msg = MIMEText("This is a test post body")
msg["Subject"] = "Test Post"
msg["From"] = gmail
msg["To"] = wp_email

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(gmail, password)
server.send_message(msg)
server.quit()
print("✓ Test email sent!")
EOF
```

---

## How It Works Internally

The updated `auto_post_wp.py` now has:

1. **`publish_to_wordpress()`** — Tries XML-RPC/REST API (original method)
2. **`publish_via_email()`** — Sends post via Gmail SMTP to WordPress
3. **`main()`** — Tries XML-RPC first, falls back to email if it fails

Flow:
```
Generate Topic → Generate Post → Try XML-RPC → (if fails) Try Email → Log result
```

---

## Differences from XML-RPC

| Feature | XML-RPC | Email |
|---------|---------|-------|
| **Speed** | Instant | 1-2 minutes |
| **Post Status** | Draft created directly | Email processed, draft created |
| **Formatting** | Full HTML support | Basic HTML support |
| **Review** | Optional | Recommended (check drafts) |
| **Tags** | Via XML-RPC API | Manual (add after) |

---

## Next Steps

1. ✅ Enable Post by Email in WordPress
2. ✅ Create Gmail app password
3. ✅ Update `.env` with credentials
4. ✅ Run `python3 auto_post_wp.py`
5. ✅ Check WordPress Drafts for new posts
6. ✅ Schedule with cron or GitHub Actions

---

## Schedule Automated Posts

### Option 1: macOS/Linux Cron

```bash
crontab -e
# Add: 0 9 * * * cd /Users/vinaybilla/Desktop/ai-agent-blogger && python3 auto_post_wp.py
```

### Option 2: GitHub Actions

See `SETUP_AND_TROUBLESHOOTING.md` for full instructions.

---

## Support

If issues persist:
1. Check `.env` has all required variables
2. Verify Gmail 2FA and app password are set up correctly
3. Confirm WordPress Post by Email is enabled
4. Run the setup helper: `python3 setup_email_posting.py`
5. Check WordPress logs or contact hosting support

