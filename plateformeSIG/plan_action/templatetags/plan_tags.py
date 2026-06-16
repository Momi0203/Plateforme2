from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """{{ my_dict|dict_get:key }}"""
    try:
        return d[key]
    except (KeyError, TypeError):
        return None


@register.filter
def list_index(lst, idx):
    """{{ my_list|list_index:forloop.counter0 }}"""
    try:
        return lst[int(idx)]
    except (IndexError, TypeError, ValueError):
        return ''
