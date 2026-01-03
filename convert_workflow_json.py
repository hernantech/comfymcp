#!/usr/bin/env python3
"""
Fetch and convert workflow_json documentation to markdown.
"""

import urllib.request
import re
import os
from html.parser import HTMLParser


class MarkdownConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.skip_depth = 0
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript'}
        self.in_main = False
        self.tag_stack = []
        self.in_code = False
        self.in_pre = False
        self.code_lang = ''
        self.list_depth = 0
        self.in_table = False
        self.table_row = []
        self.table_data = []
        self.in_header_row = False
        self.current_link_href = ''

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '')

        if tag in self.skip_tags:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        # Check for main content area
        if tag == 'main' or tag == 'article' or 'prose' in class_name:
            self.in_main = True

        if not self.in_main:
            return

        self.tag_stack.append(tag)

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.output.append('\n\n' + '#' * level + ' ')
        elif tag == 'p':
            self.output.append('\n\n')
        elif tag == 'pre':
            self.in_pre = True
            # Try to get language from class
            if 'language-' in class_name:
                match = re.search(r'language-(\w+)', class_name)
                if match:
                    self.code_lang = match.group(1)
            self.output.append('\n\n```' + self.code_lang + '\n')
        elif tag == 'code':
            if not self.in_pre:
                self.output.append('`')
            else:
                # Check for language in code tag
                if 'language-' in class_name:
                    match = re.search(r'language-(\w+)', class_name)
                    if match:
                        self.code_lang = match.group(1)
            self.in_code = True
        elif tag == 'ul':
            self.list_depth += 1
            self.output.append('\n')
        elif tag == 'ol':
            self.list_depth += 1
            self.output.append('\n')
        elif tag == 'li':
            indent = '  ' * (self.list_depth - 1)
            self.output.append('\n' + indent + '- ')
        elif tag == 'strong' or tag == 'b':
            self.output.append('**')
        elif tag == 'em' or tag == 'i':
            self.output.append('*')
        elif tag == 'a':
            self.current_link_href = attrs_dict.get('href', '')
            self.output.append('[')
        elif tag == 'br':
            self.output.append('\n')
        elif tag == 'table':
            self.in_table = True
            self.table_data = []
        elif tag == 'thead':
            self.in_header_row = True
        elif tag == 'tr':
            self.table_row = []
        elif tag == 'th' or tag == 'td':
            pass  # Will handle in handle_data
        elif tag == 'blockquote':
            self.output.append('\n\n> ')
        elif tag == 'hr':
            self.output.append('\n\n---\n\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return

        if not self.in_main:
            return

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.output.append('\n')
        elif tag == 'pre':
            self.in_pre = False
            self.output.append('\n```\n')
            self.code_lang = ''
        elif tag == 'code':
            self.in_code = False
            if not self.in_pre:
                self.output.append('`')
        elif tag == 'ul' or tag == 'ol':
            self.list_depth -= 1
        elif tag == 'strong' or tag == 'b':
            self.output.append('**')
        elif tag == 'em' or tag == 'i':
            self.output.append('*')
        elif tag == 'a':
            if self.current_link_href:
                self.output.append('](' + self.current_link_href + ')')
            else:
                self.output.append(']')
            self.current_link_href = ''
        elif tag == 'thead':
            self.in_header_row = False
        elif tag == 'tr':
            if self.table_row:
                self.table_data.append((self.table_row[:], self.in_header_row))
        elif tag == 'table':
            self.in_table = False
            if self.table_data:
                self.output.append('\n\n')
                for row, is_header in self.table_data:
                    self.output.append('| ' + ' | '.join(row) + ' |\n')
                    if is_header:
                        self.output.append('| ' + ' | '.join(['---'] * len(row)) + ' |\n')
                self.output.append('\n')
        elif tag == 'p':
            self.output.append('\n')

    def handle_data(self, data):
        if self.skip_depth > 0:
            return
        if not self.in_main:
            return

        text = data
        if not self.in_pre and not self.in_code:
            text = ' '.join(text.split())

        if self.in_table and self.tag_stack and self.tag_stack[-1] in ['td', 'th']:
            self.table_row.append(text.strip())
        elif text:
            self.output.append(text)

    def get_markdown(self):
        result = ''.join(self.output)
        # Clean up the markdown
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()
        return result


def main():
    url = 'https://docs.comfy.org/specs/workflow_json'

    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    with urllib.request.urlopen(req, timeout=60) as response:
        html = response.read().decode('utf-8')

    print(f"Received {len(html)} bytes")

    # Convert to markdown
    converter = MarkdownConverter()
    converter.feed(html)
    markdown = converter.get_markdown()

    # Create output directory if needed
    output_path = '/data/research/comfymcp/docs/specs/workflow_json.md'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"Written to {output_path}")
    print(f"Markdown length: {len(markdown)} characters")

    # Print preview
    print("\n--- Preview (first 2000 chars) ---\n")
    print(markdown[:2000])


if __name__ == '__main__':
    main()
