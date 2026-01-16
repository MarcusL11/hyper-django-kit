"""
Tests for blogs app, including XSS protection in markdown filter.
"""

import pytest
from django.test import TestCase
from django.template import Context, Template


class MarkdownFilterXSSTestCase(TestCase):
    """
    Test XSS protection in the markdown template filter.
    Ensures malicious HTML is sanitized before rendering.
    """

    def test_markdown_sanitizes_script_tags(self):
        """
        Script tags should be removed from markdown output.
        The text content inside script tags is preserved (stripped, not escaped).
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = "Hello <script>alert('XSS')</script> World"
        context = Context({"content": malicious_content})
        result = template.render(context)

        # Script tag should be stripped completely
        assert "<script>" not in result
        assert "</script>" not in result
        # Text content is preserved but tags are removed
        assert "Hello" in result
        assert "World" in result

    def test_markdown_sanitizes_onclick_attribute(self):
        """
        Event handlers like onclick should be removed.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<a href="#" onclick="alert(\'XSS\')">Click me</a>'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # onclick attribute should be stripped
        assert "onclick" not in result
        assert "alert('XSS')" not in result
        # Link should still be present but safe
        assert '<a href="#">Click me</a>' in result

    def test_markdown_allows_safe_tags(self):
        """
        Safe HTML tags should be allowed through.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        safe_content = "# Heading\n\n**Bold** and *italic*\n\n- List item"
        context = Context({"content": safe_content})
        result = template.render(context)

        # Check allowed tags are present
        assert "<h1>" in result
        assert "<strong>" in result
        assert "<em>" in result
        assert "<ul>" in result
        assert "<li>" in result

    def test_markdown_sanitizes_iframe(self):
        """
        Iframe tags should be removed.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<iframe src="http://evil.com"></iframe>'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # iframe should be stripped
        assert "<iframe" not in result
        assert "evil.com" not in result

    def test_markdown_sanitizes_img_onerror(self):
        """
        Image tags with onerror handlers should have the handler removed.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<img src="x" onerror="alert(\'XSS\')">'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # onerror should be stripped, but img tag itself is not in ALLOWED_TAGS
        # so the entire tag should be removed
        assert "onerror" not in result
        assert "alert('XSS')" not in result

    def test_markdown_preserves_safe_links(self):
        """
        Safe links with href and title attributes should be preserved.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        safe_content = '[Click here](https://example.com "Example Site")'
        context = Context({"content": safe_content})
        result = template.render(context)

        # Link should be present with allowed attributes
        assert 'href="https://example.com"' in result
        assert 'title="Example Site"' in result
        assert "Click here" in result

    def test_markdown_sanitizes_javascript_protocol(self):
        """
        Links with javascript: protocol should be sanitized.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<a href="javascript:alert(\'XSS\')">Click</a>'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # javascript: protocol should be removed/sanitized
        assert "javascript:" not in result
        assert "alert('XSS')" not in result

    def test_markdown_preserves_code_blocks(self):
        """
        Code blocks should be preserved and safe.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        code_content = "```python\nprint('Hello')\n```"
        context = Context({"content": code_content})
        result = template.render(context)

        # Code blocks should be present
        assert "<pre>" in result or "<code>" in result
        assert "print('Hello')" in result

    def test_markdown_sanitizes_style_attribute(self):
        """
        Style attributes should be removed as they're not in ALLOWED_ATTRIBUTES.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<p style="background: url(javascript:alert(\'XSS\'))">Text</p>'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # style attribute should be stripped
        assert "style=" not in result
        assert "javascript:" not in result
        assert "alert('XSS')" not in result

    def test_markdown_sanitizes_data_attributes(self):
        """
        Data attributes should be removed as they're not in ALLOWED_ATTRIBUTES.
        """
        template = Template("{% load markdown_extras %}{{ content|markdown }}")
        malicious_content = '<p data-bind="alert(\'XSS\')">Text</p>'
        context = Context({"content": malicious_content})
        result = template.render(context)

        # data attributes should be stripped
        assert "data-bind" not in result
        assert "alert('XSS')" not in result
