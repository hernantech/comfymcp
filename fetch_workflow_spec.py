#!/usr/bin/env python3
import urllib.request
import ssl
import re
from html.parser import HTMLParser
import os

class MarkdownExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content = []
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'button', 'svg', 'path'}
        self.skip_depth = 0
        self.tag_stack = []
        self.in_code = False
        self.in_pre = False
        self.list_depth = 0
        self.code_lang = ''
        self.in_main = False
        self.main_depth = 0
        self.link_href = ''
        self.table_header_row = False
        self.table_col_count = 0
        self.current_col = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '') or ''
        id_name = attrs_dict.get('id', '') or ''

        # Skip navigation and UI elements by class/id
        if ('nav' in class_name or 'sidebar' in class_name or 'menu' in class_name or
            'toc' in class_name or 'breadcrumb' in class_name or 'header' in id_name or
            'footer' in id_name or 'search' in class_name):
            self.skip_depth += 1
            return

        # Skip certain tags entirely
        if tag in self.skip_tags:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        # Track main content area
        if tag == 'main' or tag == 'article' or 'content' in class_name or 'markdown' in class_name:
            self.in_main = True
            self.main_depth += 1

        self.tag_stack.append(tag)

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.content.append('\n\n' + '#' * level + ' ')
        elif tag == 'p':
            self.content.append('\n\n')
        elif tag == 'br':
            self.content.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.content.append('**')
        elif tag == 'em' or tag == 'i':
            self.content.append('*')
        elif tag == 'code':
            if not self.in_pre:
                self.content.append('`')
            self.in_code = True
        elif tag == 'pre':
            self.in_pre = True
            lang = ''
            if class_name and 'language-' in class_name:
                match = re.search(r'language-(\w+)', class_name)
                if match:
                    lang = match.group(1)
            self.code_lang = lang
            self.content.append('\n\n```' + lang + '\n')
        elif tag == 'a':
            self.link_href = attrs_dict.get('href', '')
            self.content.append('[')
        elif tag == 'ul':
            self.list_depth += 1
            self.content.append('\n')
        elif tag == 'ol':
            self.list_depth += 1
            self.content.append('\n')
        elif tag == 'li':
            indent = '  ' * (self.list_depth - 1)
            self.content.append('\n' + indent + '- ')
        elif tag == 'table':
            self.content.append('\n\n')
            self.table_header_row = True
            self.table_col_count = 0
        elif tag == 'thead':
            self.table_header_row = True
        elif tag == 'tbody':
            self.table_header_row = False
        elif tag == 'tr':
            self.content.append('|')
            self.current_col = 0
        elif tag == 'th':
            self.table_col_count += 1
            self.content.append(' ')
        elif tag == 'td':
            self.content.append(' ')
        elif tag == 'blockquote':
            self.content.append('\n\n> ')
        elif tag == 'hr':
            self.content.append('\n\n---\n\n')

    def handle_endtag(self, tag):
        attrs_class = ''

        if tag in self.skip_tags:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_depth > 0:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if tag == 'main' or tag == 'article':
            self.main_depth = max(0, self.main_depth - 1)
            if self.main_depth == 0:
                self.in_main = False

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag == 'strong' or tag == 'b':
            self.content.append('**')
        elif tag == 'em' or tag == 'i':
            self.content.append('*')
        elif tag == 'code':
            if not self.in_pre:
                self.content.append('`')
            self.in_code = False
        elif tag == 'pre':
            self.in_pre = False
            self.content.append('\n```\n')
        elif tag == 'a':
            if self.link_href and not self.link_href.startswith('#'):
                self.content.append('](' + self.link_href + ')')
            else:
                self.content.append(']')
            self.link_href = ''
        elif tag == 'ul' or tag == 'ol':
            self.list_depth = max(0, self.list_depth - 1)
            self.content.append('\n')
        elif tag == 'li':
            pass  # newline already added at start
        elif tag == 'th':
            self.content.append(' |')
        elif tag == 'td':
            self.content.append(' |')
        elif tag == 'tr':
            self.content.append('\n')
        elif tag == 'thead':
            # Add separator row after header
            if self.table_col_count > 0:
                self.content.append('|' + ' --- |' * self.table_col_count + '\n')
            self.table_header_row = False
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.content.append('\n')

    def handle_data(self, data):
        if self.skip_depth > 0:
            return
        text = data
        if not self.in_pre and not self.in_code:
            text = ' '.join(text.split())
        if text:
            self.content.append(text)

    def get_markdown(self):
        result = ''.join(self.content)
        # Clean up multiple newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        # Clean up spaces around code blocks
        result = re.sub(r' +```', '```', result)
        # Clean up empty list items
        result = re.sub(r'\n- \n', '\n', result)
        return result.strip()

# Fetch the page
ctx = ssl.create_default_context()
url = "https://docs.comfy.org/specs/workflow_json_0.4"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

print(f"Fetching {url}...")
with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
    html = response.read().decode('utf-8')
    print(f"Fetched {len(html)} bytes")

# Parse and convert to markdown
parser = MarkdownExtractor()
parser.feed(html)
markdown = parser.get_markdown()

# Create output directory
os.makedirs('/data/research/comfymcp/docs/specs', exist_ok=True)

# Write the markdown file
output_path = '/data/research/comfymcp/docs/specs/workflow_json_0.4.md'
with open(output_path, 'w') as f:
    f.write(markdown)

print(f"Saved to {output_path}")
print(f"Content length: {len(markdown)} characters")
