from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='split')
def split_filter(value, delimiter=','):
    if value:
        return [s.strip() for s in str(value).split(delimiter) if s.strip()]
    return []


@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (TypeError, ValueError):
        return value


@register.filter
def multiply(value, arg):
    try:
        return int(float(value) * float(arg))
    except (TypeError, ValueError):
        return 0


@register.filter
def percentage(value, total):
    try:
        return int(float(value) / float(total) * 100)
    except (TypeError, ZeroDivisionError):
        return 0


@register.simple_tag
def match_ring(score, size=56):
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    r      = (size / 2) - 5
    circ   = 2 * 3.14159 * r
    offset = circ * (1 - score / 100)
    if score >= 85:
        color = '#1E6B40'
    elif score >= 70:
        color = '#C9A84C'
    elif score >= 50:
        color = '#B86010'
    else:
        color = '#B83230'
    svg = (
        '<div class="match-ring" style="width:%dpx;height:%dpx">'
        '<svg viewBox="0 0 %d %d" style="transform:rotate(-90deg)">'
        '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#E8E6DF" stroke-width="5"/>'
        '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="5"'
        ' stroke-dasharray="%.1f" stroke-dashoffset="%.1f" stroke-linecap="round"/>'
        '</svg>'
        '<div class="match-ring-label" style="color:%s;font-size:%dpx;font-weight:700">%d%%</div>'
        '</div>'
    ) % (
        size, size, size, size,
        size/2, size/2, r,
        size/2, size/2, r, color,
        circ, offset,
        color, max(10, size//5), score
    )
    return mark_safe(svg)


@register.filter
def get_item(dictionary, key):
    """Récupère une valeur dans un dict par clé depuis un template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0


@register.filter
def strip(value):
    """Strip whitespace from a string."""
    return str(value).strip()


@register.filter(name='pluralize_fr')
def pluralize_fr(count, forms=''):
    """Pluralisation française : count|pluralize_fr:'candidat,candidats'"""
    try:
        singular, plural = forms.split(',')
        return singular if int(count) <= 1 else plural
    except Exception:
        return ''
