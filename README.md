# Gmail + WordPress Post-by-Email Setup

This project uses **Gmail SMTP** to send blog posts to **WordPress Post-by-Email** for automatic publishing.

## Architecture

```
Gemini API (Generate Topics & Posts)
        ↓
Gmail SMTP (Send Email)
        ↓
WordPress Post-by-Email (Create Draft Post)
        ↓
WordPress Blog
```

## Prerequisites

1. **Gmail Account** with 2-factor authentication enabled
2. **Gmail App Password** (generated for this application)
3. **WordPress Blog** with Post-by-Email enabled
4. **Google Gemini API Key** (for content generation)
5. **Python 3.7+**

## Environment Setup

### 1. Create `.env` file in project root

```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail SMTP Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# WordPress Post-by-Email
WP_EMAIL_ADDRESS=your-post-by-email@post.wordpress.com
WP_SITE=https://yourwordpressblog.com
WP_USER=your-wordpress-username
WORDPRESS_TOKEN=your-wordpress-app-password
```

### 2. Generate Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already done
3. Search for "App passwords"
4. Select "Mail" and "Windows Computer" (or your device)
5. Copy the 16-character password and use it as `GMAIL_APP_PASSWORD`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## How It Works

### Content Generation (Gemini)
1. Generates a developer-focused blog topic
2. Writes a 500-1000 word blog post about the topic
3. Formats with HTML for rich formatting

### Email Sending (Gmail SMTP)
1. Sends the blog post via Gmail SMTP (smtp.gmail.com:465)
2. Email goes to WordPress Post-by-Email address
3. HTML formatting is preserved

### Publishing (WordPress)
1. WordPress receives email via Post-by-Email feature
2. Email subject becomes post title
3. Email body becomes post content
4. Post is saved as draft (can be reviewed before publishing)

## Running the Script

### Local Testing

```bash
python3 auto_post_wp.py
```

Expected output:
```
INFO Starting auto-post flow
INFO Topic: [Generated Topic]
INFO Generated post
INFO Connecting to smtp.gmail.com:465
INFO Sending to: your-post-by-email@post.wordpress.com
INFO Subject: [Post Title]
INFO Body length: XXXX chars
INFO ✓ Email sent successfully
INFO Done. Result: {...}
```

### Automated Publishing (GitHub Actions)

The project includes a GitHub Actions workflow that runs daily at 09:00 UTC.

**Workflow file**: `.github/workflows/schedule_publish.yml`

**Required GitHub Secrets**:
- `GEMINI_API_KEY`: Your Gemini API key
- `GMAIL_USER`: Your Gmail email address
- `GMAIL_APP_PASSWORD`: Your 16-character Gmail app password
- `WP_EMAIL_ADDRESS`: Your WordPress Post-by-Email address
- `WP_SITE`: Your WordPress site URL
- `WP_USER`: Your WordPress username
- `WORDPRESS_TOKEN`: Your WordPress app password


## Troubleshooting

### Gmail Authentication Error: "Login with app passwords only"

**Solution**: Ensure you're using an app-specific password, not your regular Gmail password
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new 16-character app password for Gmail
3. Update `GMAIL_APP_PASSWORD` in `.env`

### Post content appears as draft in WordPress

**Expected behavior**: WordPress Post-by-Email creates drafts by default so you can review before publishing.
- You must manually publish drafts in WordPress admin

### Email not received by WordPress

**Debugging**:
1. Check Gmail account for bounce/delivery issues
2. Verify `WP_EMAIL_ADDRESS` is correct
3. Ensure WordPress Post-by-Email is enabled (Settings → Post by Email in WordPress admin)
4. Check spam folder in WordPress Post-by-Email inbox

### SMTP Connection Timeout

**Solutions**:
- Verify Gmail app password is correct (16 characters)
- Ensure 2-factor authentication is enabled on Gmail account
- Check firewall isn't blocking port 465
- Verify GMAIL_USER matches your Gmail address

## File Structure

```
auto_post_wp.py              # Main script
requirements.txt             # Python dependencies
.env                         # Environment variables (secret)
.github/
  workflows/
    schedule_publish.yml     # GitHub Actions automation
publish_log.jsonl            # Log of published posts
```

## Key Features

✅ **Fully Automated**: Topic generation, content creation, and publishing
✅ **Gmail SMTP**: Reliable email delivery via Gmail
✅ **Developer Content**: Focused on tech, programming, DevOps, and more
✅ **Scheduled Publishing**: Daily automation via GitHub Actions
✅ **Audit Trail**: `publish_log.jsonl` tracks all posts
✅ **HTML Support**: Rich text formatting in email body

## Customization

### Change Publishing Schedule

Edit `.github/workflows/schedule_publish.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # Change to your desired time (UTC)
```

### Modify Topic Generation

Edit the `choose_topic()` function in `auto_post_wp.py` to customize topic categories.

### Adjust Post Length

Edit the `generate_post()` function - change `"500-1000 word"` to your preferred length.

## Support

For SendGrid issues: https://support.sendgrid.com
For WordPress issues: https://wordpress.com/support
For Gemini API issues: https://ai.google.dev/docs
