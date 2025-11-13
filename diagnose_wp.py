#!/usr/bin/env python3
"""
Diagnostic script to test WordPress XML-RPC connection and credentials.
Run this to troubleshoot authentication issues.

Usage: python3 diagnose_wp.py
"""

import os
import sys
import xmlrpc.client
import ssl
from dotenv import load_dotenv

# Load env variables
load_dotenv()

WP_SITE = os.getenv("WP_SITE", "").strip('"').strip("'")
WP_USER = os.getenv("WP_USER", "").strip('"').strip("'")
WP_APP_PASS = os.getenv("WORDPRESS_TOKEN", "").strip('"').strip("'")

print("=" * 70)
print("WORDPRESS XML-RPC DIAGNOSTIC TOOL")
print("=" * 70)

# Check 1: Verify environment variables
print("\n[CHECK 1] Environment Variables")
print("-" * 70)
if not WP_SITE:
    print("❌ WP_SITE not set")
    sys.exit(1)
if not WP_USER:
    print("❌ WP_USER not set")
    sys.exit(1)
if not WP_APP_PASS:
    print("❌ WORDPRESS_TOKEN not set")
    sys.exit(1)

print(f"✓ WP_SITE: {WP_SITE}")
print(f"✓ WP_USER: {WP_USER}")
print(f"✓ WORDPRESS_TOKEN: {'*' * len(WP_APP_PASS)} ({len(WP_APP_PASS)} chars)")

# Check 2: Determine XML-RPC endpoint
print("\n[CHECK 2] XML-RPC Endpoint")
print("-" * 70)
if "wordpress.com" in WP_SITE:
    xmlrpc_url = "https://wordpress.com/xmlrpc.php"
    print(f"✓ Detected WordPress.com site")
else:
    xmlrpc_url = f"{WP_SITE}/xmlrpc.php"
    print(f"✓ Detected self-hosted WordPress")

print(f"✓ XML-RPC URL: {xmlrpc_url}")

# Check 3: Test XML-RPC connectivity
print("\n[CHECK 3] XML-RPC Connectivity")
print("-" * 70)
try:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    server = xmlrpc.client.ServerProxy(xmlrpc_url, context=ssl_context, verbose=False)
    print(f"✓ Connected to {xmlrpc_url}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Check 4: Test authentication
print("\n[CHECK 4] Authentication Test")
print("-" * 70)
try:
    blogs = server.wp.getUsersBlogs(WP_USER, WP_APP_PASS)
    print(f"✓ Authenticated successfully!")
    print(f"✓ Number of blogs: {len(blogs)}")
    
    if blogs:
        for blog in blogs:
            print(f"\n  Blog: {blog['blogName']}")
            print(f"    URL: {blog['url']}")
            print(f"    Blog ID: {blog['blogid']}")
            print(f"    XML-RPC URL: {blog['xmlrpc']}")
    else:
        print("\n⚠️  No blogs found for this user!")
        print("   Make sure the blog is associated with this WordPress.com account.")
        print("   OR try using XML-RPC endpoint of your blog directly:")
        print(f"   https://your-blog.wordpress.com/xmlrpc.php")
        
except xmlrpc.client.Fault as e:
    print(f"❌ Authentication failed: {e}")
    print("\n   Possible issues:")
    if "401" in str(e):
        print("   - Invalid username or password")
        print("   - App password may be expired")
        print("   - Username might be different from blog slug")
    elif "403" in str(e):
        print("   - XML-RPC is disabled on this blog")
        print("   - Check Settings → Writing → Enable Remote Publishing")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

# Check 5: Test post creation
print("\n[CHECK 5] Test Post Creation")
print("-" * 70)

if not blogs:
    print("⚠️  Skipping (no blogs available)")
else:
    blog_id = blogs[0]['blogid']
    print(f"Using blog ID: {blog_id}")
    
    test_post = {
        "post_title": "[TEST] Auto-Post Script Test",
        "post_content": "This is a test post created by the diagnostic script.",
        "post_status": "draft",
    }
    
    try:
        post_id = server.metaWeblog.newPost(blog_id, WP_USER, WP_APP_PASS, test_post)
        print(f"✓ Test post created successfully!")
        print(f"✓ Post ID: {post_id}")
        print(f"✓ URL: {blogs[0]['url']}/?p={post_id}")
        print("\n   This post is saved as a DRAFT. You can view it in your WordPress dashboard.")
        
    except xmlrpc.client.Fault as e:
        print(f"❌ Failed to create post: {e}")
        print("\n   Possible issues:")
        if "401" in str(e):
            print("   - You don't have permission to publish on this blog")
            print("   - Try using a different user account")
        elif "403" in str(e):
            print("   - XML-RPC is disabled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED! Your WordPress setup is working correctly.")
print("=" * 70)
print("\nYou can now run: python3 auto_post_wp.py")
