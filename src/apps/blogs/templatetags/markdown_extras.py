"""
Custom template tags for markdown rendering in blog templates.
"""

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.safestring import mark_safe

import markdown as md
import bleach

register = template.Library()

# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "img",  # Required for markdown images
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"], "img": ["src", "alt"]}


@register.filter(name="markdown")
@stringfilter
def markdown(value):
    """
    Convert markdown text to HTML with XSS protection.
    Uses the same markdown extensions configured in settings.
    HTML output is sanitized using bleach to prevent XSS attacks.
    """
    extensions = getattr(
        settings,
        "MARKDOWNX_MARKDOWN_EXTENSIONS",
        [
            "markdown.extensions.extra",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
        ],
    )
    # Convert markdown to HTML
    html = md.markdown(value, extensions=extensions)
    # Sanitize HTML to prevent XSS attacks
    sanitized = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return mark_safe(sanitized)


@register.filter(name="reading_time")
def reading_time(word_count):
    """
    Calculate estimated reading time in minutes from word count.
    Assumes average reading speed of 200 words per minute.

    Args:
        word_count: Number of words (integer)

    Returns:
        Estimated reading time in minutes (minimum 1)

    Example:
        {% with word_count=blog.content|wordcount %}
        {{ word_count|reading_time }} min read
        {% endwith %}
    """
    try:
        word_count = int(word_count)
        if word_count <= 0:
            return 1
        minutes = max(1, round(word_count / 200))
        return minutes
    except (ValueError, TypeError):
        return 1
