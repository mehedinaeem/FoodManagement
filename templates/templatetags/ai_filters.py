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

