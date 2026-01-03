#!/usr/bin/env python3
"""Fetch workflow_json docs - extracts content from Next.js data or HTML."""
import urllib.request
import ssl
import re
import json
import os

def extract_next_data(html):
    """Extract content from __NEXT_DATA__ script tag."""
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            # Navigate to page content - structure varies by site
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            # Look for mdx content or page content
            content = page_props.get('mdxSource', '')
            if not content:
                content = page_props.get('content', '')
            if not content:
                content = page_props.get('markdownContent', '')
            if not content:
                # Try to find frontMatter or other content
                frontmatter = page_props.get('frontMatter', {})
                if frontmatter:
                    content = f"# {frontmatter.get('title', 'Untitled')}\n\n"
                    content += frontmatter.get('description', '') + "\n\n"
            return content, data
        except json.JSONDecodeError:
            pass
    return None, None

def extract_mdx_content(html):
    """Extract MDX/Markdown-like content from page."""
    # Look for content in article or main tags
    main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
    article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)

    content = main_match.group(1) if main_match else (article_match.group(1) if article_match else html)

    # Remove script tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    # Remove style tags
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    # Remove nav tags
    content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL)
    # Remove svg tags
    content = re.sub(r'<svg[^>]*>.*?</svg>', '', content, flags=re.DOTALL)

    return content

def html_to_markdown(html):
    """Convert HTML to basic markdown."""
    content = html

    # Convert headers
    for i in range(6, 0, -1):
        content = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', '\n\n' + '#' * i + r' \1\n', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1\n', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert code blocks
    content = re.sub(r'<pre[^>]*><code[^>]*class="[^"]*language-(\w+)[^"]*"[^>]*>(.*?)</code></pre>',
                     r'\n\n```\1\n\2\n```\n', content, flags=re.DOTALL|re.IGNORECASE)
    content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>',
                     r'\n\n```\n\1\n```\n', content, flags=re.DOTALL|re.IGNORECASE)
    content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n\n```\n\1\n```\n', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert inline code
    content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert strong/bold
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL|re.IGNORECASE)
    content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert emphasis/italic
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL|re.IGNORECASE)
    content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert links
    content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert list items
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', content, flags=re.DOTALL|re.IGNORECASE)

    # Convert blockquotes
    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n\n> \1\n', content, flags=re.DOTALL|re.IGNORECASE)

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Decode HTML entities
    content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    content = content.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')

    # Clean up whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    content = '\n'.join(line.strip() for line in content.split('\n'))

    return content.strip()

url = 'https://docs.comfy.org/specs/workflow_json'
ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
        html = response.read().decode('utf-8')
        print(f"FETCHED {len(html)} bytes")

    # Save raw HTML for debugging
    with open('/tmp/workflow_json_raw.html', 'w') as f:
        f.write(html)
    print("SAVED RAW HTML to /tmp/workflow_json_raw.html")

    # Try to extract Next.js data first
    next_content, next_data = extract_next_data(html)

    if next_data:
        # Save the JSON data for inspection
        with open('/tmp/workflow_json_data.json', 'w') as f:
            json.dump(next_data, f, indent=2)
        print("SAVED NEXT DATA to /tmp/workflow_json_data.json")

    if next_content:
        markdown = next_content
        print("Extracted content from __NEXT_DATA__")
    else:
        # Fall back to HTML parsing
        html_content = extract_mdx_content(html)
        markdown = html_to_markdown(html_content)
        print("Extracted content from HTML")

    output_path = '/data/research/comfymcp/docs/specs/workflow_json.md'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(markdown)
    print(f"SAVED TO {output_path}")
    print(f"MARKDOWN LENGTH: {len(markdown)} characters")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
