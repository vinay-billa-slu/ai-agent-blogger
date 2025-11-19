# Content Generation Guide

This guide explains how to customize topic generation and blog post creation for your WordPress blog.

## Overview

The auto-posting system generates content in two stages:

1. **Topic Generation** (`choose_topic()`) - Creates a developer-focused blog topic
2. **Post Generation** (`generate_post()`) - Writes a 500-1000 word blog post on that topic

Both use Google Gemini API for content creation, with built-in category rotation and topic deduplication.

## Topic Generation

### How Topics Are Generated

Topics are generated with **automatic category rotation** to ensure diverse content:

```python
TECH_CATEGORIES = [
    "Programming Languages",
    "Frameworks & Libraries",
    "Databases & Data Engineering",
    "DevOps & Infrastructure",
    "System Design & Architecture",
    "Performance & Optimization",
    "Security & Best Practices",
    "Emerging Tech & Tools",
    "Software Engineering Practices",
    "Career & Productivity"
]
```

**Rotation:** Each run picks the next category in order. After 10 runs, the cycle repeats.

**Deduplication:** Topics are never generated twice. The system tracks all previously generated topics in `topic_tracker.json` and explicitly avoids them.

### Example Topics

| Category | Example Topic |
|----------|--------------|
| Programming Languages | "Understanding Python Decorators and Their Real-World Use Cases" |
| Frameworks & Libraries | "React Hooks Best Practices: Beyond useState and useEffect" |
| Databases & Data Engineering | "PostgreSQL JSON Operators: Advanced Query Patterns" |
| DevOps & Infrastructure | "Kubernetes Networking: Service Discovery and Load Balancing" |
| System Design & Architecture | "Event-Driven Architecture: When and How to Implement" |
| Performance & Optimization | "Profiling Python Applications: CPU and Memory Analysis" |
| Security & Best Practices | "Secure API Design: Authentication, Authorization, and Rate Limiting" |
| Emerging Tech & Tools | "Getting Started with Rust: WebAssembly for Web Development" |
| Software Engineering Practices | "Code Review Best Practices: Building a Strong Engineering Culture" |
| Career & Productivity | "Burnout Prevention for Software Engineers: Practical Strategies" |

### Customizing Categories

To add or modify categories, edit `auto_post_wp.py`:

```python
TECH_CATEGORIES = [
    "Programming Languages",
    "Frameworks & Libraries",
    "Databases & Data Engineering",
    "DevOps & Infrastructure",
    "System Design & Architecture",
    "Performance & Optimization",
    "Security & Best Practices",
    "Emerging Tech & Tools",
    "Software Engineering Practices",
    "Career & Productivity",
    # ADD NEW CATEGORIES HERE:
    "Machine Learning & AI",
    "Cloud Platforms",
]
```

After modifying:
1. Delete or reset `topic_tracker.json` to start fresh
2. Run `python3 auto_post_wp.py --dry-run` to generate a topic from your new categories

### Forcing a Specific Topic

If you want to generate a post on a specific topic (not auto-generated):

```bash
# Modify auto_post_wp.py temporarily:
# In main(), change:
# topic = choose_topic()
# To:
# topic = "Your Custom Topic Here"

python3 auto_post_wp.py --dry-run --show
```

Then revert the change.

## Post Generation

### How Posts Are Generated

The `generate_post()` function uses Gemini API with a detailed prompt to:

1. **Generate 500-1000 words** of developer-focused content
2. **Include 3-5 real, working code examples** with proper syntax highlighting
3. **Format in markdown** for proper rendering in WordPress
4. **Avoid placeholders** (auto-regenerates if it detects `CODEBLOCK_0` tokens)
5. **Handle truncation** (auto-continues if output is incomplete)

### Post Structure

Each generated post typically includes:

```markdown
# Why This Matters
[Introductory paragraph explaining the relevance]

# Key Concepts
[Explanation of the main topic with markdown formatting]

```bash
# Code example 1
echo "First example"
```

# Best Practices
[Practical advice and tips]

```python
# Code example 2
def example():
    print("Second example")
```

# Conclusion
[Summary and next steps]
```

### Markdown Features

Posts use the following markdown that WordPress Post-by-Email will render as HTML:

| Markdown | HTML | Renders As |
|----------|------|-----------|
| `# Heading` | `<h5>` | Large bold heading with blue underline |
| `**bold text**` | `<strong>` | **Bold text** |
| `*italic text*` | `<em>` | *Italic text* |
| `` `inline code` `` | `<code>` with background | `monospace with gray background` |
| `* Bullet point` | `<ul><li>` | • Bullet point |
| Triple backticks with language | `<pre><code>` | Styled code block with language label |

### Code Block Examples

The post generation prompt ensures real, working code:

```bash
# Bash example
curl -X GET https://api.example.com/users
```

```python
# Python example
import json
data = {"name": "Alice", "role": "Engineer"}
print(json.dumps(data, indent=2))
```

```yaml
# YAML example
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: my-container
    image: my-image:latest
```

### Customizing Post Generation

#### 1. Change Post Length

Edit `auto_post_wp.py` and modify the `generate_post()` prompt:

```python
# Current:
prompt = f"""Write a 500-1000 word blog post about: {topic}

# Change to:
prompt = f"""Write a 1000-1500 word blog post about: {topic}
```

#### 2. Change Code Examples Count

Edit the prompt requirement:

```python
# Current:
- Include 3-5 real, working code examples with proper syntax

# Change to:
- Include 6-8 real, working code examples with proper syntax
```

#### 3. Change Target Audience Tone

Edit the AUDIENCE & TONE section:

```python
# Current:
AUDIENCE & TONE:
- Write for software developers and engineers
- Use an engaging, conversational tone

# Change to (e.g., for beginners):
AUDIENCE & TONE:
- Write for junior developers learning new concepts
- Use a clear, educational tone with step-by-step explanations
- Avoid advanced jargon without explanation
```

#### 4. Add Required Topics

Modify the CONTENT REQUIREMENTS:

```python
# Add something like:
- Always include a "Common Mistakes" section
- End with 3 resource links (blog posts, documentation, tutorials)
```

### Handling Failed Generations

The system automatically handles common issues:

#### Placeholder Tokens (CODEBLOCK_0, etc.)

If Gemini generates placeholders instead of real code:

```
[REGEN ATTEMPT 1/3] Model generated literal CODEBLOCK_N placeholders instead of real code. 
Requesting full regeneration.
```

The system:
1. Detects placeholder tokens
2. Requests a full regeneration with explicit instructions
3. Retries up to 3 times
4. Falls back to wrapping placeholders if still present

#### Truncated Output

If the output looks incomplete (ends without punctuation):

```
Output looks truncated; attempting continuation (attempt 1)
```

The system:
1. Detects incomplete sentences/code
2. Requests continuation from where it left off
3. Retries up to 3 times

### Monitoring Generation Quality

Check the logs while generating:

```bash
python3 auto_post_wp.py --dry-run --show 2>&1 | grep -E "REGEN|truncated|✓"
```

Look for:
- ✅ `✓ Generated topic` - Topic created successfully
- ✅ `✓ No placeholders in final output` - Post generation succeeded without issues
- ⚠️ `[REGEN ATTEMPT 1/3]` - Post had to be regenerated (may happen 1-2 times)
- ❌ `After all regeneration attempts, still have placeholders` - Fallback used (rare)

## Post Publishing Flow

After generation, posts are:

1. **Converted to HTML** - Markdown formatted as styled HTML
2. **Sent via Gmail SMTP** - To WordPress Post-by-Email address
3. **Received by WordPress** - Automatically creates a Draft post
4. **Recorded in logs** - Saved to `publish_log.jsonl`
5. **Reviewable** - Available in WordPress Admin for manual review before publishing

## Performance Considerations

### API Rates and Costs

- **Gemini API**: Free tier includes generous limits. Check [Google AI Studio](https://aistudio.google.com)
- **Topic generation**: ~1-2 seconds per call
- **Post generation**: ~10-15 seconds per call
- **Total per run**: ~15-20 seconds

### Caching Strategy

The system uses `topic_tracker.json` to avoid regenerating the same topics. This:
- Reduces API calls
- Ensures content diversity
- Allows you to "reset" if desired by deleting the file

## Troubleshooting Content Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Posts too short (< 500 words) | Model may have been interrupted | Use `--show` to inspect; regenerate if needed |
| Placeholder tokens in output | Gemini API issue | System auto-regenerates; check logs for `[REGEN ATTEMPT]` |
| Code examples missing language | Markdown parsing issue | Check logs; retry generation |
| Topics repeating | `topic_tracker.json` corrupted | Delete file: `rm topic_tracker.json` |
| Generic/repetitive topics | Category rotation cycle | Add more categories; diversify TECH_CATEGORIES |
| Gemini API errors | Rate limit or authentication | Check GEMINI_API_KEY in `.env`; wait and retry |

## Next Steps

- See [SETUP.md](SETUP.md) to configure API keys
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing generated content
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging
