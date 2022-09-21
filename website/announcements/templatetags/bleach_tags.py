from bleach.css_sanitizer import CSSSanitizer
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from bleach import clean

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def bleach(value):
    """Bleach dangerous html from the input."""
    css_sanitizer = CSSSanitizer(allowed_css_properties=["text-decoration"])
    return mark_safe(
        clean(
            value,
            tags=[
                "h2",
                "h3",
                "p",
                "a",
                "div",
                "strong",
                "em",
                "i",
                "b",
                "ul",
                "li",
                "br",
                "ol",
                "span",
            ],
            attributes={
                "*": ["class", "style"],
                "a": ["href", "rel", "target", "title"],
            },
            css_sanitizer=css_sanitizer,
            strip=True,
        )
    )
