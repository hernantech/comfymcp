#!/usr/bin/env python3
import urllib.request
import ssl
import re
from html.parser import HTMLParser

class MarkdownExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content = []
        self.skip_depth = 0
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'button', 'svg'}
        self.nav_classes = {'sidebar', 'toc', 'navigation', 'navbar', 'breadcrumb', 'menu'}
        self.tag_stack = []
        self.in_code_block = False
        self.code_lang = ''
        self.code_content = []
        self.list_depth = 0
        self.in_table = False
        self.table_rows = []
        self.current_row = []
        self.is_header_row = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '').lower()
        id_name = attrs_dict.get('id', '').lower()

        if tag in self.skip_tags:
            self.skip_depth += 1
            return

        if any(nav in class_name for nav in self.nav_classes) or any(nav in id_name for nav in self.nav_classes):
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        self.tag_stack.append(tag)

        if tag == 'pre':
            self.in_code_block = True
            self.code_content = []
        elif tag == 'code' and not self.in_code_block:
            self.content.append('`')
        elif tag == 'code' and self.in_code_block:
            if 'class' in attrs_dict:
                for cls in attrs_dict['class'].split():
                    if cls.startswith('language-'):
                        self.code_lang = cls[9:]
                        break
                    elif cls.startswith('lang-'):
                        self.code_lang = cls[5:]
                        break
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
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
        elif tag == 'a':
            href = attrs_dict.get('href', '')
            self.content.append('[')
            self.tag_stack[-1] = ('a', href)
        elif tag == 'ul' or tag == 'ol':
            self.list_depth += 1
            self.content.append('\n')
        elif tag == 'li':
            indent = '  ' * (self.list_depth - 1)
            self.content.append(f'\n{indent}- ')
        elif tag == 'table':
            self.in_table = True
            self.table_rows = []
        elif tag == 'thead':
            self.is_header_row = True
        elif tag == 'tr':
            self.current_row = []
        elif tag in ('th', 'td'):
            pass
        elif tag == 'blockquote':
            self.content.append('\n\n> ')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return

        if not self.tag_stack:
            return

        current = self.tag_stack.pop()

        if tag == 'pre':
            lang = self.code_lang or ''
            code = ''.join(self.code_content)
            self.content.append(f'\n\n```{lang}\n{code}\n```\n\n')
            self.in_code_block = False
            self.code_lang = ''
            self.code_content = []
        elif tag == 'code' and not self.in_code_block:
            self.content.append('`')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.content.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.content.append('**')
        elif tag == 'em' or tag == 'i':
            self.content.append('*')
        elif tag == 'a' and isinstance(current, tuple):
            _, href = current
            self.content.append(f']({href})')
        elif tag == 'ul' or tag == 'ol':
            self.list_depth -= 1
            self.content.append('\n')
        elif tag == 'tr':
            if self.current_row:
                self.table_rows.append(self.current_row)
        elif tag == 'thead':
            self.is_header_row = False
            if self.table_rows:
                self.table_rows.append(['---'] * len(self.table_rows[-1]))
        elif tag == 'table':
            self.in_table = False
            if self.table_rows:
                self.content.append('\n\n')
                for row in self.table_rows:
                    self.content.append('| ' + ' | '.join(row) + ' |\n')
                self.content.append('\n')
            self.table_rows = []

    def handle_data(self, data):
        if self.skip_depth > 0:
            return

        text = data

        if self.in_code_block:
            self.code_content.append(data)
        elif self.in_table and self.current_row is not None:
            stripped = text.strip()
            if stripped:
                self.current_row.append(stripped)
        else:
            text = re.sub(r'\s+', ' ', text)
            if text.strip():
                self.content.append(text)

    def get_markdown(self):
        result = ''.join(self.content)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

url = 'https://docs.comfy.org/development/comfyui-server/execution_model_inversion_guide'
ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        html = response.read().decode('utf-8')

    parser = MarkdownExtractor()
    parser.feed(html)
    markdown = parser.get_markdown()

    output_path = '/data/research/comfymcp/docs/development/comfyui-server/execution_model_inversion_guide.md'
    with open(output_path, 'w') as f:
        f.write(markdown)

    print(f"Successfully wrote {len(markdown)} characters to {output_path}")

except Exception as e:
    print(f"Error: {e}")
