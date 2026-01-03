#!/usr/bin/env python3
"""Fetch the raw markdown from GitHub."""
import urllib.request
import ssl
import json

# Try multiple possible paths for the raw markdown
urls = [
    'https://raw.githubusercontent.com/Comfy-Org/docs/main/custom-nodes/js/javascript_dialog.mdx',
    'https://raw.githubusercontent.com/Comfy-Org/docs/main/custom-nodes/js/javascript_dialog.md',
    'https://raw.githubusercontent.com/Comfy-Org/docs/main/docs/custom-nodes/js/javascript_dialog.mdx',
    'https://raw.githubusercontent.com/Comfy-Org/docs/main/docs/custom-nodes/js/javascript_dialog.md',
]

ctx = ssl.create_default_context()

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            content = response.read().decode('utf-8')

            # Clean up MDX-specific syntax for plain markdown
            # Remove import statements
            import re
            content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)
            # Remove JSX-like components but keep content
            content = re.sub(r'<Callout[^>]*>', '> **Note:**', content)
            content = re.sub(r'</Callout>', '', content)
            # Remove other component tags
            content = re.sub(r'<[A-Z][a-zA-Z]*[^>]*/>', '', content)
            # Clean up empty lines
            content = re.sub(r'\n{3,}', '\n\n', content)

            output_path = '/data/research/comfymcp/docs/custom-nodes/js/javascript_dialog.md'
            with open(output_path, 'w') as f:
                f.write(content.strip())

            print(f"Successfully fetched from {url}")
            print(f"Wrote {len(content)} characters to {output_path}")
            break
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}")
    except Exception as e:
        print(f"Error for {url}: {e}")
else:
    print("Failed to fetch from all URLs")
