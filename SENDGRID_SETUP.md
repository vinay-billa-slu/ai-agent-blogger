# SendGrid Setup Guide

## Issue: "The from address does not match a verified Sender Identity"

SendGrid requires you to verify the sender email address before you can send emails.

### Steps to Verify Sender Identity:

1. **Log in to SendGrid Dashboard**
   - Go to https://app.sendgrid.com

2. **Navigate to Sender Authentication**
   - Left sidebar → Settings → Sender Authentication
   - OR
   - Left sidebar → Marketing → Sender Authentication

3. **Verify a Sender (Single Sender Verification)**
   - Click "Create New Sender"
   - Fill in the sender details:
     - **From Email Address**: The email you want to send from (e.g., `paxep16902@agenra.com`)
     - **From Name**: Your name or brand name
     - **Reply-To Address**: (optional)
     - **Address**: Your physical address
     - **City, State, Country, Postal Code**: Your location
   - Click "Create"

4. **Verify Your Email**
   - SendGrid will send a verification email to the address you provided
   - Check your email inbox and click the verification link
   - Wait for verification to complete (can take a few minutes)

5. **Update .env file** (if needed)
   ```
   SENDER_EMAIL=paxep16902@agenra.com
   ```

6. **Test Again**
   ```bash
   python3 auto_post_wp.py
   ```

## Expected Success Response:

When successful, you should see:
```
INFO Sending email via SendGrid API
INFO Sending to: poqa173saji@post.wordpress.com
INFO Subject: [Your Blog Title]
INFO Body length (plain text): XXXX chars
INFO ✓ Email sent successfully via SendGrid
INFO Done. Result: {...}
```

## Troubleshooting:

- **Still getting 403 error**: Wait a few minutes for verification to complete in SendGrid dashboard
- **Different error**: Check your `SENDGRID_API_KEY` is correct in the .env file
- **API Key invalid**: Make sure you're using a full SendGrid API Key (starts with `SG.`), not a restricted token
