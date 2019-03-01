from django.template.defaultfilters import json_script
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment
from webpack_loader.templatetags.webpack_loader import render_bundle

from comics.templatetags.comics_extras import page_num
from comics.templatetags.image_extras import thumbgen, thumburl


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,

        'render_bundle': render_bundle,
        'thumbgen': thumbgen,
        'thumburl': thumburl,
    })
    env.filters.update({
        'json_script': json_script,
        'page_num': page_num,
    })
    return env
