from django.template.defaultfilters import json_script
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment
from webpack_loader.templatetags.webpack_loader import render_bundle

from comics.templatetags.comics_extras import page_num, oxford_comma, ugroupby
from comics.templatetags.image_extras import thumbgen, thumburl
from metadata.templatetags.metadata_extras import role_summary


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
        'oxford_comma': oxford_comma,
        'page_num': page_num,
        'role_summary': role_summary,
        'ugroupby': ugroupby,
    })
    return env
