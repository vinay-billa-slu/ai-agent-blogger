# Testing Guide

This guide covers how to test the auto-posting system locally before relying on GitHub Actions for production publishing.

## Prerequisites

- Python 3.10+
- All dependencies installed: `pip install -r requirements.txt`
- `.env` file configured with all required secrets (see [SETUP.md](SETUP.md))

## Local Testing

### 1. Quick Dry-Run Test

Test the entire flow without actually sending an email:

```bash
python3 auto_post_wp.py --dry-run
```

**What this does:**
- Generates a topic via Gemini API
- Generates a blog post via Gemini API
- Converts markdown to HTML
- Prints the email content to console
- **Does NOT send email** to WordPress

**Expected output:**
```
2025-11-19 10:30:45 INFO Starting auto-post flow
2025-11-19 10:30:45 INFO Category rotation: Programming Languages (index 1/10)
2025-11-19 10:30:48 INFO ✓ Generated topic (Category: Programming Languages): Understanding Python Decorators
2025-11-19 10:30:48 INFO Generated post
2025-11-19 10:30:58 INFO Preparing to send email via Gmail SMTP to wp-email@example.com
2025-11-19 10:30:58 INFO Subject: Understanding Python Decorators
2025-11-19 10:30:58 INFO Body length (HTML): 3250 chars
2025-11-19 10:30:58 INFO Message type: HTML (proper formatting for WordPress Post-by-Email)
2025-11-19 10:30:58 INFO HTML CONTENT (first 500 chars):
<h4 style="color: #222; font-size: 28px; margin: 0 0 20px 0;">Understanding Python Decorators</h4>
...
2025-11-19 10:30:58 INFO Dry run enabled — not sending. Message preview above.
```

### 2. Show Full Generated Post

Preview the complete generated post without sending:

```bash
python3 auto_post_wp.py --dry-run --show
```

**What this does:**
- Runs the full flow with `--dry-run`
- Prints the complete HTML email body to console
- Useful for visually inspecting formatting, headings, code blocks, etc.

**Tips:**
- Look for properly formatted section headers (`<h5>` tags)
- Verify code blocks have language labels (bash, python, javascript, etc.)
- Check that bold/italic formatting is preserved
- Ensure no placeholder text or `CODEBLOCK_0` tokens appear

### 3. Save Post to File

Generate a post and save it to a file for inspection:

```bash
python3 auto_post_wp.py --dry-run --save
```

**What this does:**
- Generates the post
- Saves to a file named `last_post_<timestamp>.txt`
- Useful for archiving generated content before sending

**Example output:**
```
$ ls -la last_post_*.txt
-rw-r--r--  1 user  group  4521 Nov 19 10:35 last_post_1729349720.txt
```

### 4. Send Test Email (Actual)

Send a real email to WordPress Post-by-Email:

```bash
python3 auto_post_wp.py
```

**What this does:**
- Generates topic and post
- Sends HTML email via Gmail SMTP to your WordPress Post-by-Email address
- Logs success/failure and records result in `publish_log.jsonl`

**Expected output on success:**
```
2025-11-19 10:35:42 INFO Starting auto-post flow
2025-11-19 10:35:42 INFO Category rotation: Frameworks & Libraries (index 2/10)
2025-11-19 10:35:45 INFO ✓ Generated topic (Category: Frameworks & Libraries): React Hooks Best Practices
2025-11-19 10:35:45 INFO Generated post
2025-11-19 10:35:58 INFO Preparing to send email via Gmail SMTP to wp-email@example.com
2025-11-19 10:35:58 INFO Subject: React Hooks Best Practices
2025-11-19 10:35:58 INFO Body length (HTML): 3150 chars
2025-11-19 10:35:58 INFO Message type: HTML (proper formatting for WordPress Post-by-Email)
2025-11-19 10:35:59 INFO ✓ Email sent successfully via Gmail SMTP (HTML with proper formatting)
2025-11-19 10:35:59 INFO Done. Result: {'post_title': 'React Hooks Best Practices', 'to': 'wp-email@example.com'}
```

### 5. Combine Options

Use multiple flags together:

```bash
# Save AND show (but don't send)
python3 auto_post_wp.py --dry-run --show --save

# Send for real AND save a copy
python3 auto_post_wp.py --save
```

## Verifying Posts in WordPress

After sending an email (without `--dry-run`), verify it appears in WordPress:

1. **Check WordPress Admin**: Go to **Posts → All Posts**
   - Look for a new **Draft** post with the generated title
   - Post should be timestamped around when you ran the script

2. **Inspect the Email**: Check your email client (Gmail) for bounce/delivery notifications
   - If email failed, you'll see an NDR (Non-Delivery Report)
   - Check Gmail's Sent folder for the email sent to WordPress

3. **Check the Post Content**:
   - WordPress should have extracted the HTML content
   - Headings should be rendered (not as raw HTML)
   - Code blocks should have syntax highlighting background
   - Bullet points should be formatted as lists
   - Bold and italic text should be styled

## Debugging

### View Logs

Check the auto-post logs (only recorded for actual sends, not `--dry-run`):

```bash
cat publish_log.jsonl | tail -5
```

**Example output:**
```json
{"topic": "Understanding Python Decorators", "result": {"post_title": "Understanding Python Decorators", "to": "wp-email@example.com"}, "ts": 1729349720}
{"topic": "React Hooks Best Practices", "result": {"post_title": "React Hooks Best Practices", "to": "wp-email@example.com"}, "ts": 1729349759}
```

### Track Generated Topics

View the topic tracker to see category rotation and used topics:

```bash
cat topic_tracker.json | python3 -m json.tool
```

**Example output:**
```json
{
  "next_category_index": 2,
  "used_topics": [
    "Understanding Python Decorators",
    "React Hooks Best Practices"
  ],
  "category_counts": {
    "Programming Languages": 1,
    "Frameworks & Libraries": 1,
    "Databases & Data Engineering": 0,
    ...
  }
}
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'google'` | Missing google-genai package | Run `pip install -r requirements.txt` |
| `GMAIL_USER not set` | Environment variables missing | Set up `.env` file (see SETUP.md) |
| `Connection timed out (smtp.gmail.com:465)` | Network/firewall issue | Check internet connection; verify Gmail SMTP is accessible |
| `(535, b'5.7.8 Username and Password not accepted')` | Wrong Gmail credentials | Verify app password is correct (not regular password) |
| `CODEBLOCK_0 or CODEBLOCK_1 in output` | Gemini failed to generate real code | Retry; model should regenerate with actual code |
| Post not appearing in WordPress | Email filtered as spam | Check WordPress spam folder; whitelist sender email |

### Enable Debug Logging

The script already logs at INFO level. For more verbose output, you can temporarily modify logging:

```python
# In auto_post_wp.py, change:
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
```

Then re-run:
```bash
python3 auto_post_wp.py --dry-run
```

## GitHub Actions Testing

### Manual Dispatch

Trigger the scheduled workflow manually from GitHub:

1. Go to **Actions** tab in your GitHub repository
2. Select **"Publish Blog Post"** workflow
3. Click **Run workflow** button
4. Select **main** branch
5. Click **Run workflow**

Check the workflow run logs to see output in real-time.

### View Workflow Runs

```bash
gh workflow view "Publish Blog Post" --json conclusion -H
```

Or view in GitHub UI:
- **Actions** → **Publish Blog Post** → Click a run to see logs

## Best Practices

✅ **Always test with `--dry-run` first** before sending production emails

✅ **Use `--show` to inspect formatting** before sending

✅ **Save posts** to archive your generated content

✅ **Monitor `publish_log.jsonl`** to track what was published

✅ **Check topic diversity** by viewing `topic_tracker.json` periodically

✅ **Run local tests weekly** to catch issues early

✅ **Monitor GitHub Actions logs** for any failures

## Next Steps

- See [SETUP.md](SETUP.md) for environment configuration
- See [CONTENT_GENERATION.md](CONTENT_GENERATION.md) for customizing post generation
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging
