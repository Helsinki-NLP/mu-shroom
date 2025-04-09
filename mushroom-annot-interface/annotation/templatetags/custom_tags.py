from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from .. import services

register = template.Library()

@register.filter(needs_autoescape=True)
def show_annots(annotation, autoescape=True):
    highlights = set()
    html_chunk = ""
    prev_start = 0
    text = annotation.datapoint.model_output.replace('\r\n', '\n')
    for span in annotation.json_highlighted_spans.strip(';').split(';'):
        if span:
            start, end = map(int, span.split(':'))
            html_chunk += text[prev_start:start]
            segment = text[start:end]
            if autoescape:
                segment = conditional_escape(segment)
            html_chunk += '<span class="selected">' + segment + '</span>'
            prev_start = end
    html_chunk += text[prev_start:]
    return mark_safe(html_chunk)


@register.filter(needs_autoescape=True)
def show_annots_annotable(annotation, autoescape=True):
    highlights = set()
    html_chunk = ""
    prev_start = 0
    text = annotation.datapoint.model_output
    for span in annotation.json_highlighted_spans.strip(';').split(';'):
        if span:
            start, end = map(int, span.split(':'))
            html_chunk += text[prev_start:start]
            segment = text[start:end]
            if autoescape:
                segment = conditional_escape(segment)
            html_chunk += '<span class="removable selected">' + segment + '</span>'
            prev_start = end
    html_chunk += text[prev_start:]
    return mark_safe(html_chunk)

