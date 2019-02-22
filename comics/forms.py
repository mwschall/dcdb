import json
import re
from decimal import Decimal
from json import JSONDecodeError

from django.forms import FileInput, ImageField, RegexField
from django.forms.widgets import FILE_INPUT_CONTRADICTION
from django.utils.translation import gettext_lazy as _

from comics.models import GenericImage
from comics.util import unpack_numeral

CROPPIE_VERSION = '2.6.3'
# TODO: install and manage croppie via npm


class CroppieInput(FileInput):
    template_name = 'comics/forms/widgets/croppie.html'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/croppie/%s/croppie.css' % CROPPIE_VERSION,
                'comics/croppieField.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/croppie/%s/croppie.min.js' % CROPPIE_VERSION,
            'comics/croppieField.js',
        )

    def format_value(self, value):
        if isinstance(value, GenericImage):
            return json.dumps({
                'url': value.src.url,
                'points': value.box,
            })

    def value_from_datadict(self, data, files, name):
        upload = super().value_from_datadict(data, files, name)
        try:
            data = json.loads(data[name + '_crop'])
            box = [int(p) for p in data['points']]
            if upload:
                upload.box = box
        except (KeyError, JSONDecodeError):
            # same basic logic as ClearableFileInput
            if not self.is_required:
                if upload:
                    # TODO: this should be a custom error
                    return FILE_INPUT_CONTRADICTION
                return False
            return None
        return upload

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if isinstance(value, GenericImage):
            context['widget']['preview'] = value.scaled.url
        return context


class CroppieField(ImageField):
    widget = CroppieInput
    # TODO: a validator for the returned crop box points

    def __init__(self, *, crop_size, **kwargs):
        self.crop_size = crop_size
        super().__init__(**kwargs)

    def to_python(self, data):
        f = super().to_python(data)
        if f is not None:
            # is maybe not correct to return a model field here, but
            # does make things cleaner
            return GenericImage(src=f, box=f.box, size=self.crop_size)

    def run_validators(self, value):
        super().run_validators(value and value.src)


class NumeralField(RegexField):
    # TODO: validate number of decimals in each part
    default_regex = re.compile(r'^(\d+)(?:\s*[-\.]\s*(\d+)?)?$')
    default_error_messages = {
        'invalid': _('A value like 7 or 7-11 or 7.11 is expected.'),
    }

    def __init__(self, *, first_length, second_length, **kwargs):
        self.max_digits = first_length + second_length
        self.decimal_places = second_length
        kwargs['strip'] = True
        kwargs['empty_value'] = None
        super().__init__(self.default_regex, **kwargs)

    def prepare_value(self, value):
        s = unpack_numeral(value, self.decimal_places)
        return s if s is not None else value

    def to_python(self, data):
        value = super().to_python(data)
        try:
            m = re.match(self.regex, value)
            a = Decimal(m.group(1))
            b = Decimal(m.group(2) or 0) / pow(10, self.decimal_places)
            return a + b
        except (AttributeError, TypeError):
            return value

