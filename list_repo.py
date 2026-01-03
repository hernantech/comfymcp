#!/usr/bin/env python3
"""List the GitHub repo contents."""
import urllib.request
import ssl
import json

url = 'https://api.github.com/repos/Comfy-Org/docs/contents'
ctx = ssl.create_default_context()

try:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        content = response.read().decode('utf-8')
        data = json.loads(content)
        print("Root contents:")
        for item in data:
            print(f"  {item['type']}: {item['name']}")
except Exception as e:
    print(f"Error: {e}")
