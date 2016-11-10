import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def page_num(page):
    return 'cover' if page.is_cover else '{:03d}'.format(page.number)


@register.filter(name='json')
def json_dumps(data):
    return mark_safe(json.dumps(data, separators=(',', ':')))
