# Troubleshooting Guide

Comprehensive troubleshooting for common issues with the AI Agent Blogger system.

## Table of Contents

1. [Setup Issues](#setup-issues)
2. [API & Authentication Issues](#api--authentication-issues)
3. [Email & SMTP Issues](#email--smtp-issues)
4. [WordPress Post-by-Email Issues](#wordpress-post-by-email-issues)
5. [Content Generation Issues](#content-generation-issues)
6. [GitHub Actions Issues](#github-actions-issues)
7. [Performance & Logging](#performance--logging)
8. [Advanced Debugging](#advanced-debugging)

---

## Setup Issues

### Issue: "ModuleNotFoundError: No module named 'google'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'google'
```

**Causes:**
- Dependencies not installed
- Wrong Python virtual environment

**Solutions:**

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python3 -c "import google; print(google.__version__)"
   ```

3. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.10+
   ```

4. **Verify you're in virtual environment:**
   ```bash
   which python3  # Should show venv/bin/python3
   ```

### Issue: "No module named 'dotenv'"

**Solutions:**
```bash
pip install python-dotenv
```

### Issue: ".env file not found"

**Symptoms:**
```
Error loading .env: No such file or directory
```

**Solutions:**

1. **Create `.env` file:**
   ```bash
   touch .env
   ```

2. **Add required variables:**
   ```bash
   cat > .env << 'EOF'
   GEMINI_API_KEY=your-key
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-password
   WP_EMAIL_ADDRESS=publish-xxx@example.wordpress.com
   EOF
   ```

3. **Verify file exists:**
   ```bash
   cat .env
   ```

---

## API & Authentication Issues

### Issue: "GEMINI_API_KEY not set"

**Symptoms:**
```
Error: Missing GEMINI_API_KEY
Exiting...
```

**Causes:**
- Environment variable not set
- `.env` file missing or empty
- `.env` file not in project root

**Solutions:**

1. **Check `.env` file:**
   ```bash
   cat .env | grep GEMINI_API_KEY
   ```

2. **Get a new API key:**
   - Go to [Google AI Studio](https://aistudio.google.com)
   - Click **"Get API key"**
   - Create in Google Cloud Console
   - Copy the full key

3. **Update `.env`:**
   ```bash
   echo "GEMINI_API_KEY=your-new-key-here" >> .env
   ```

4. **Test the key:**
   ```bash
   python3 << 'EOF'
   from google import genai
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   api_key = os.getenv("GEMINI_API_KEY")
   
   if not api_key:
       print("✗ API key not found in environment")
   else:
       try:
           client = genai.Client(api_key=api_key)
           response = client.models.generate_content(
               model="gemini-2.0-flash",
               contents="Test"
           )
           print("✓ Gemini API works!")
       except Exception as e:
           print(f"✗ Gemini API error: {e}")
   EOF
   ```

### Issue: "Gemini API error: 403 Permission denied"

**Causes:**
- Invalid API key
- API key has no quota
- API not enabled in Google Cloud

**Solutions:**

1. **Verify API key:**
   ```bash
   curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}'
   ```

2. **Check quota:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Select your project
   - Go to **Quotas & System Limits**
   - Check Generative Language API quotas

3. **Enable API:**
   - Go to Google Cloud Console
   - Search for "Generative Language API"
   - Click **Enable**

### Issue: "Gemini API error: 429 Resource exhausted"

**Symptoms:**
```
Too many requests. Please wait before retrying.
```

**Causes:**
- Exceeded API rate limit (free tier: 15 requests per minute)
- GitHub Actions hitting the limit across multiple runs

**Solutions:**

1. **Wait before retrying:**
   ```bash
   sleep 60 && python3 auto_post_wp.py
   ```

2. **Space out runs:**
   - Modify GitHub Actions cron to run less frequently
   - Use single daily run instead of multiple

3. **Check usage:**
   - Go to [Google AI Studio](https://aistudio.google.com)
   - Check request history
   - View quota limits

4. **Upgrade if needed:**
   - Switch to paid Google Cloud plan for higher quotas

---

## Email & SMTP Issues

### Issue: "GMAIL_USER or GMAIL_APP_PASSWORD not set"

**Solutions:**

1. **Verify in `.env`:**
   ```bash
   grep -E "GMAIL_USER|GMAIL_APP_PASSWORD" .env
   ```

2. **Add credentials:**
   ```bash
   echo "GMAIL_USER=your-email@gmail.com" >> .env
   echo "GMAIL_APP_PASSWORD=your-16-char-password" >> .env
   ```

3. **Verify app password (16 characters, no spaces):**
   ```bash
   cat .env | grep GMAIL_APP_PASSWORD | wc -c  # Should be ~40 (16 + newline + prefix)
   ```

### Issue: "Connection timed out (smtp.gmail.com:465)"

**Symptoms:**
```
Traceback (most recent call last):
  ...
socket.timeout: _ssl.c:1003: The handshake operation timed out
```

**Causes:**
- Network connectivity issue
- Firewall blocking port 465
- Gmail SMTP server temporarily unavailable

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping gmail.com
   ```

2. **Test SMTP port:**
   ```bash
   nc -zv smtp.gmail.com 465  # Should output "succeeded"
   ```

3. **Try with longer timeout:**
   - Edit `auto_post_wp.py`
   - Change `timeout=30` to `timeout=60` in `publish_via_gmail()`

4. **Check firewall:**
   ```bash
   # macOS
   sudo lsof -i :465  # Check if port is accessible
   
   # Check if your ISP blocks port 465
   # Try different network (mobile hotspot) to test
   ```

5. **Try Gmail SMTP alternatives:**
   ```python
   # In auto_post_wp.py, try port 587 instead of 465:
   server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
   server.starttls()
   ```

### Issue: "(535, b'5.7.8 Username and Password not accepted')"

**Symptoms:**
```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Causes:**
- Wrong Gmail email or app password
- Using regular Gmail password instead of app password
- 2FA not enabled (required for app passwords)

**Solutions:**

1. **Verify 2FA is enabled:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Scroll to "2-Step Verification"
   - If disabled, enable it first

2. **Generate new app password:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Scroll to "App passwords"
   - Select "Mail" and "Windows Computer"
   - Generate new password
   - Copy exactly (16 characters, remove spaces)

3. **Update `.env`:**
   ```bash
   # Remove old password
   sed -i '' '/GMAIL_APP_PASSWORD=/d' .env
   
   # Add new password
   echo "GMAIL_APP_PASSWORD=new-16-char-password" >> .env
   ```

4. **Test SMTP connection:**
   ```bash
   python3 << 'EOF'
   import smtplib
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   
   gmail_user = os.getenv("GMAIL_USER")
   gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
   
   try:
       server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
       server.login(gmail_user, gmail_pass)
       print("✓ Authentication successful")
       server.quit()
   except smtplib.SMTPAuthenticationError as e:
       print(f"✗ Authentication failed: {e}")
   except Exception as e:
       print(f"✗ Connection error: {e}")
   EOF
   ```

### Issue: "550 5.1.1 The email account that you tried to reach does not exist"

**Symptoms:**
```
smtplib.SMTPRecipientsRefused: {recipient: (550, b'5.1.1 ... does not exist')}
```

**Causes:**
- Wrong WordPress Post-by-Email address
- WordPress Post-by-Email not set up correctly

**Solutions:**

1. **Verify WordPress Post-by-Email:**
   - Log in to WordPress Admin
   - Go to **Settings** → **Post-by-Email**
   - Copy the exact email address shown

2. **Update `.env`:**
   ```bash
   sed -i '' '/WP_EMAIL_ADDRESS=/d' .env
   echo "WP_EMAIL_ADDRESS=publish-xxxxx@example.wordpress.com" >> .env
   ```

3. **Test with dry-run:**
   ```bash
   python3 auto_post_wp.py --dry-run --show
   ```

---

## WordPress Post-by-Email Issues

### Issue: "Post-by-Email not enabled in WordPress"

**Symptoms:**
- No "Settings → Post-by-Email" option in WordPress Admin
- Feature not available on your plan

**Solutions:**

1. **Check WordPress.com plan:**
   - Post-by-Email only available on WordPress.com Business plan or higher
   - Or self-hosted WordPress with proper configuration

2. **Enable on self-hosted:**
   - Edit `wp-config.php`
   - Add: `define('WPCOM_API_CACHE', false);`
   - Ensure Post-by-Email plugin is active

3. **Alternative:** Use WordPress REST API
   - Requires WordPress plugin/theme support
   - See [README.md](README.md) for REST API setup

### Issue: "Email arrives but no post created in WordPress"

**Symptoms:**
- Email appears in Gmail Sent folder
- No draft post appears in WordPress Admin

**Causes:**
- Email filtered as spam
- Post-by-Email settings incorrect
- Email formatting issues

**Solutions:**

1. **Check WordPress spam:**
   - WordPress Admin → **Discussions** → **Spam Comments**
   - Look for the email content
   - Mark as "Not Spam"

2. **Whitelist sender email:**
   - WordPress Admin → Settings → Post-by-Email
   - Add your Gmail address to trusted senders (if supported)

3. **Check email headers:**
   - Forward the email to WordPress support
   - Ask about email filtering rules

4. **Verify Post-by-Email settings:**
   - WordPress Admin → Settings → Post-by-Email
   - Ensure "Publish automatically" is disabled (posts as draft)
   - Ensure category is set correctly

5. **Test with simple email:**
   ```bash
   # Send simple text email to WordPress
   python3 << 'EOF'
   import smtplib
   from email.mime.text import MIMEText
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   
   gmail_user = os.getenv("GMAIL_USER")
   gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
   wp_email = os.getenv("WP_EMAIL_ADDRESS")
   
   msg = MIMEText("Simple test post body", 'plain')
   msg['Subject'] = "Simple Test Post"
   msg['From'] = gmail_user
   msg['To'] = wp_email
   
   server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
   server.login(gmail_user, gmail_pass)
   server.sendmail(gmail_user, [wp_email], msg.as_string())
   server.quit()
   
   print("✓ Test email sent")
   EOF
   ```

### Issue: "Post formatting is wrong in WordPress"

**Symptoms:**
- Headers not bold
- Code blocks showing raw HTML
- Bullet points not formatted

**Causes:**
- WordPress not recognizing HTML email
- Email client settings

**Solutions:**

1. **Verify HTML email is sent:**
   ```bash
   python3 auto_post_wp.py --dry-run --show | head -50
   ```
   - Should see `<h5>`, `<strong>`, `<code>` tags

2. **Check WordPress Post-by-Email settings:**
   - Some setups strip HTML
   - May need to adjust theme or settings

3. **Use alternative: REST API**
   - Provides more control over post formatting
   - See [README.md](README.md)

---

## Content Generation Issues

### Issue: "CODEBLOCK_0 or CODEBLOCK_1 in output"

**Symptoms:**
```
This technique is useful for CODEBLOCK_0, especially when dealing with asynchronous operations.
```

**Causes:**
- Gemini generated placeholder instead of real code
- Model interrupted or hit token limit

**Solutions:**

1. **Automatic regeneration:**
   - System detects this and automatically regenerates
   - Check logs for `[REGEN ATTEMPT]` messages
   - Usually resolves on second attempt

2. **Manual regeneration:**
   ```bash
   # Delete topic to force new generation
   # Edit auto_post_wp.py temporarily to use a new topic
   python3 auto_post_wp.py --dry-run --show
   ```

3. **Check logs:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 | grep -E "REGEN|placeholder|CODEBLOCK"
   ```

4. **If still failing:**
   - May indicate API rate limit or quota issue
   - Check Gemini API quota
   - Try again after waiting 1 minute

### Issue: "Post output is truncated or incomplete"

**Symptoms:**
```
# Conclusion
This approach provides significant...
```
- Post ends abruptly mid-sentence

**Causes:**
- Gemini API hit token limit
- Output truncation detection failed

**Solutions:**

1. **Check logs for continuation attempts:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 | grep "truncated\|continuation"
   ```

2. **Verify post with --show:**
   ```bash
   python3 auto_post_wp.py --dry-run --show | tail -20
   ```

3. **Reduce post length:**
   - Edit `auto_post_wp.py`
   - Change `500-1000 word` to `400-800 word` in prompt
   - Reduce `max_output_tokens`

### Issue: "Same topics repeating"

**Symptoms:**
- Topics like "Python Decorators" generated multiple times
- Not rotating through categories

**Causes:**
- `topic_tracker.json` corrupted
- First-time setup (small sample size)

**Solutions:**

1. **View topic history:**
   ```bash
   cat topic_tracker.json | python3 -m json.tool
   ```

2. **Reset tracker:**
   ```bash
   rm topic_tracker.json
   ```

3. **Verify rotation:**
   ```bash
   for i in {1..10}; do python3 auto_post_wp.py --dry-run 2>&1 | grep "Category rotation"; done
   ```
   - Should see different categories each time

### Issue: "Topics are too generic or off-topic"

**Causes:**
- Gemini using default generic topics
- Category prompt not specific enough

**Solutions:**

1. **Add category context:**
   - Edit `choose_topic()` in `auto_post_wp.py`
   - Make prompt more specific to desired angle

2. **Customize categories:**
   - Add more specific categories to `TECH_CATEGORIES`
   - Remove overly broad categories

3. **Test topics manually:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 | grep "Generated topic"
   ```

---

## GitHub Actions Issues

### Issue: "Workflow not running at scheduled time"

**Causes:**
- Workflow disabled
- Cron syntax incorrect
- GitHub Actions disabled for repo

**Solutions:**

1. **Enable GitHub Actions:**
   - Repository → **Settings** → **Actions** → **General**
   - Ensure "Allow all actions" is selected

2. **Check workflow file:**
   ```bash
   cat .github/workflows/schedule_publish.yml | grep -A 2 "schedule:"
   ```

3. **Verify cron syntax:**
   - Should be: `cron: '0 9 * * *'`
   - Check with [crontab.guru](https://crontab.guru)

4. **Manual trigger test:**
   - GitHub → **Actions** → **Publish Blog Post**
   - Click **Run workflow** → **Run workflow**

### Issue: "Workflow fails with missing dependencies"

**Symptoms:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Causes:**
- `requirements.txt` not installed in workflow
- Syntax error in workflow file

**Solutions:**

1. **Verify workflow installs deps:**
   ```yaml
   # .github/workflows/schedule_publish.yml should have:
   - name: Install dependencies
     run: pip install -r requirements.txt
   ```

2. **Check requirements.txt:**
   ```bash
   cat requirements.txt
   ```
   - Should contain: `google-genai`, `python-dotenv`, `markdown`

3. **Test locally:**
   ```bash
   pip install -r requirements.txt
   python3 auto_post_wp.py --dry-run
   ```

### Issue: "Workflow secrets not found"

**Symptoms:**
```
Error: GEMINI_API_KEY not set
```

**Causes:**
- GitHub secrets not configured
- Wrong secret names in workflow

**Solutions:**

1. **Add secrets:**
   - Repository → **Settings** → **Secrets and variables** → **Actions**
   - Add: `GEMINI_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `WP_EMAIL_ADDRESS`

2. **Verify secret names match workflow:**
   ```yaml
   # .github/workflows/schedule_publish.yml should have:
   env:
     GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
     GMAIL_USER: ${{ secrets.GMAIL_USER }}
     GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
     WP_EMAIL_ADDRESS: ${{ secrets.WP_EMAIL_ADDRESS }}
   ```

3. **Test locally with same env vars:**
   ```bash
   export GEMINI_API_KEY="..."
   export GMAIL_USER="..."
   # etc
   python3 auto_post_wp.py --dry-run
   ```

---

## Performance & Logging

### Issue: "Script running very slowly"

**Causes:**
- Gemini API slow
- Network latency
- Regeneration attempts

**Solutions:**

1. **Check generation logs:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 | grep -E "attempt|REGEN|seconds"
   ```

2. **Typical timings:**
   - Topic generation: 2-3 seconds
   - Post generation: 10-15 seconds
   - Total: 15-20 seconds

3. **If taking > 30 seconds:**
   - Check network: `ping google.com`
   - Check API status: [Google Cloud Status](https://status.cloud.google.com)
   - Try again after 1 minute

### Issue: "Want to increase logging verbosity"

**Solutions:**

1. **Edit logging level temporarily:**
   ```python
   # In auto_post_wp.py, change:
   logging.basicConfig(level=logging.INFO, ...)
   # To:
   logging.basicConfig(level=logging.DEBUG, ...)
   ```

2. **Run with debug output:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 | grep -i "debug\|error\|warn"
   ```

---

## Advanced Debugging

### Enable Full Python Traceback

```bash
python3 -u auto_post_wp.py --dry-run 2>&1 | tee debug.log
```

This creates `debug.log` with full output for analysis.

### Test Individual Components

#### Test Topic Generation Only

```python
python3 << 'EOF'
from auto_post_wp import choose_topic
topic = choose_topic()
print(f"Generated topic: {topic}")
EOF
```

#### Test Post Generation Only

```python
python3 << 'EOF'
from auto_post_wp import generate_post
post = generate_post("Test Topic: Python Decorators")
print(post['title'])
print(post['body_html'][:500])
EOF
```

#### Test Email Sending Only

```python
python3 << 'EOF'
from auto_post_wp import publish_via_gmail
import os
from dotenv import load_dotenv

load_dotenv()

post = {
    'title': 'Test Post',
    'body_html': '# Test\n\nThis is a test post with **bold** text.'
}

try:
    result = publish_via_gmail(post, dry_run=True, show=True)
    print("✓ Email send test successful")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

### Inspect Generated Files

```bash
# View topic history
cat topic_tracker.json | python3 -m json.tool

# View publish log
cat publish_log.jsonl | tail -1 | python3 -m json.tool

# View saved posts
ls -lh last_post_*.txt
```

### Contact Support

If issues persist:

1. **Check GitHub Issues:** https://github.com/vinay-billa-slu/ai-agent-blogger/issues
2. **Collect debug info:**
   ```bash
   python3 auto_post_wp.py --dry-run 2>&1 > debug.log
   # Include debug.log in issue report (remove secrets!)
   ```
3. **Provide environment:**
   ```bash
   python3 --version
   pip list | grep -E "google-genai|python-dotenv|markdown"
   ```

---

## Next Steps

- See [SETUP.md](SETUP.md) for configuration help
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing strategies
- See [CONTENT_GENERATION.md](CONTENT_GENERATION.md) for customization
