from django import template

register = template.Library()


@register.filter
def page_num(page):
    return 'cover' if page.is_cover else '{:03d}'.format(page.number)
