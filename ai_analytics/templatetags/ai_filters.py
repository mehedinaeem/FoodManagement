from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def replace(value, arg):
    """Replace string in value."""
    old, new = arg.split(',')
    return value.replace(old, new)


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def abs(value):
    """Get absolute value of a number."""
    try:
        import math
        return math.fabs(float(value))
    except (ValueError, TypeError):
        return 0

