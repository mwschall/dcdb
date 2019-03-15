from django import template

register = template.Library()


@register.filter
def role_summary(credit_list, total=0):
    def fmt_credit(c):
        if not total or c.role_count == total:
            return c.role_name
        return '{} ({})'.format(c.role_name, c.role_count)

    return [fmt_credit(c) for c in credit_list]
