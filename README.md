# SendGrid + WordPress Post-by-Email Setup

This project uses **SendGrid** (email service) to send blog posts to **WordPress Post-by-Email** for automatic publishing.

## Architecture

```
Gemini API (Generate Topics & Posts)
        ↓
SendGrid API (Send Email)
        ↓
WordPress Post-by-Email (Create Draft Post)
        ↓
WordPress Blog
```

## Prerequisites

1. **SendGrid Account** (free tier available at https://sendgrid.com)
2. **WordPress Blog** with Post-by-Email enabled
3. **Google Gemini API Key** (for content generation)
4. **Python 3.7+**

## Environment Setup

### 1. Create `.env` file in project root

```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# SendGrid Configuration
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
SENDER_EMAIL=your-verified-email@example.com

# WordPress Post-by-Email
WP_EMAIL_ADDRESS=your-post-by-email@post.wordpress.com
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify SendGrid Sender Email

See `SENDGRID_SETUP.md` for detailed instructions on verifying your sender email.

## How It Works

### Content Generation (Gemini)
1. Generates a developer-focused blog topic
2. Writes a 500-1000 word blog post about the topic
3. Formats as plain text (no HTML)

### Email Sending (SendGrid)
1. Sends the blog post via SendGrid API
2. Email goes to WordPress Post-by-Email address
3. Plain text formatting is preserved

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
INFO Starting auto-post (fixed) flow
INFO Topic: [Generated Topic]
INFO Generated post
INFO Sending email via SendGrid API
INFO Sending to: your-post-by-email@post.wordpress.com
INFO Subject: [Post Title]
INFO Body length (plain text): XXXX chars
INFO ✓ Email sent successfully via SendGrid
INFO Done. Result: {...}
```

### Automated Publishing (GitHub Actions)

The project includes a GitHub Actions workflow that runs daily at 09:00 UTC.

**Workflow file**: `.github/workflows/schedule_publish.yml`

**Required GitHub Secrets**:
- `GEMINI_API_KEY`: Your Gemini API key
- `SENDGRID_API_KEY`: Your SendGrid API key  
- `SENDER_EMAIL`: Your verified SendGrid sender email
- `WP_EMAIL_ADDRESS`: Your WordPress Post-by-Email address

## Troubleshooting

### SendGrid Error: "from address does not match a verified Sender Identity"

**Solution**: Verify your sender email in SendGrid dashboard
- See `SENDGRID_SETUP.md` for step-by-step instructions

### Post content appears as draft in WordPress

**Expected behavior**: WordPress Post-by-Email creates drafts by default so you can review before publishing.
- You must manually publish drafts in WordPress admin

### Email not received by WordPress

**Debugging**:
1. Check SendGrid logs: https://app.sendgrid.com/email_activity
2. Verify `WP_EMAIL_ADDRESS` is correct
3. Ensure WordPress Post-by-Email is enabled (Settings → Post by Email in WordPress admin)

### Content looks incorrect in WordPress

**Common issues**:
- Plain text formatting may not render as expected
- Use clear paragraph breaks (double newlines) for readability
- Lists, headers, and code blocks should be clearly marked in plain text

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
✅ **Plain Text Focus**: No HTML stripping issues like Gmail
✅ **Reliable Email**: SendGrid has 99.99% uptime SLA
✅ **Developer Content**: Focused on tech, programming, DevOps, and more
✅ **Scheduled Publishing**: Daily automation via GitHub Actions
✅ **Audit Trail**: `publish_log.jsonl` tracks all posts

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
