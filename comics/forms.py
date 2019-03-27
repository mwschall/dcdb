import json
import re
from decimal import Decimal
from io import BytesIO
from json import JSONDecodeError
from pathlib import Path

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import FileInput, ImageField, RegexField, Widget, FileField, ClearableFileInput
from django.utils.translation import gettext_lazy as _

from comics.util import unpack_numeral, s_uuid, get_upload_fp
from comics.validators import validate_installment_extension

CROPPIE_VERSION = '2.6.3'
# TODO: install and manage croppie via npm

IMAGE_CROP_CONTRADICTION = object()


class MicroModal(Widget):
    class Media:
        css = {
            'all': (
                'admin/css/micromodal.css',
            )
        }
        js = (
            'https://unpkg.com/micromodal/dist/micromodal.min.js',
        )


class CroppieInput(MicroModal, FileInput):
    template_name = 'admin/widgets/croppie.html'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/croppie/%s/croppie.css' % CROPPIE_VERSION,
                'admin/css/croppieField.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/croppie/%s/croppie.min.js' % CROPPIE_VERSION,
            'admin/js/croppieField.js',
        )

    def __init__(self, *, preview_size=(50, 50), circular_viewport=False, **kwargs):
        self.preview_size = preview_size
        self.circular_viewport = circular_viewport
        super().__init__(**kwargs)

    def format_value(self, value):
        if value:
            return value.url

    def value_from_datadict(self, data, files, name):
        upload = super().value_from_datadict(data, files, name)
        crop_val = data[name + '_crop']
        try:
            crop_data = json.loads(crop_val)
            box = [int(p) for p in crop_data['points']]
            if upload:
                upload.box = box
        except (KeyError, JSONDecodeError):
            # same basic logic as ClearableFileInput
            if not self.is_required and not crop_val:
                if upload:
                    return IMAGE_CROP_CONTRADICTION
                return False
            return None
        return upload

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['preview_width'] = self.preview_size[0]
        context['widget']['preview_height'] = self.preview_size[1]
        context['widget']['viewport'] = json.dumps({
            'type': 'circle' if self.circular_viewport else 'square',
        })
        return context


class CroppieField(ImageField):
    widget = CroppieInput
    default_error_messages = {
        'crop_confusion': _('Needs more crop-age.')
    }
    # TODO: a validator for the returned crop box points

    def to_python(self, data):
        # let ImageField to its thing
        f = super().to_python(data)
        if f is None:
            return None

        # rename to avoid conflicts in the currently flat storage scheme
        uuid_name = s_uuid()

        # don't crop unless necessary
        if f.box is None or f.box == [0, 0, f.image.width, f.image.height]:
            f.name = '{}{}'.format(uuid_name, Path(f.name).suffix)
            return f

        # gotta reopen because Image.verify() consumes the file pointer
        file = get_upload_fp(data)

        # crop and save as optimized png for best-est qualities
        buf = BytesIO()
        with Image.open(file) as src:
            src.crop(f.box).save(buf, 'PNG', optimize=True)
        fc = InMemoryUploadedFile(buf, None, '{}.png'.format(uuid_name), 'image/png', buf.tell(), None)
        return fc

    def clean(self, data, initial=None):
        if data is IMAGE_CROP_CONTRADICTION:
            raise ValidationError(self.error_messages['crop_confusion'], code='crop_confusion')
        return super().clean(data, initial)


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


class InstallmentFileField(FileField):
    widget = ClearableFileInput(attrs={'multiple': True, 'accept': 'image/*,.pdf,.zip'})
    default_validators = [validate_installment_extension]
