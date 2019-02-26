import json

from django import template
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def page_num(page):
    return 'cover' if page.is_cover else '{:03d}'.format(page.number)


@register.filter(name='json')
def json_dumps(data):
    return mark_safe(json.dumps(data, separators=(',', ':')))


# https://stackoverflow.com/a/52749486
# noinspection PyUnboundLocalVariable
@register.filter(is_safe=True, needs_autoescape=True)
def oxford_comma(items, autoescape=True):
    """Join together items in a list, separating them with commas or ', and'"""
    items = map(force_text, items)
    if autoescape:
        items = map(conditional_escape, items)

    items = list(items)
    num_items = len(items)
    if num_items == 0:
        s = ''
    elif num_items == 1:
        s = items[0]
    elif num_items == 2:
        s = items[0] + ' and ' + items[1]
    elif num_items > 2:
        for i, item in enumerate(items):
            if i == 0:
                # First item
                s = item
            elif i == (num_items - 1):
                # Last item.
                s += ', and ' + item
            else:
                # Items in the middle
                s += ', ' + item

    return mark_safe(s)
