import json
from json import JSONDecodeError

from django.forms import FileInput, ImageField
from django.forms.widgets import FILE_INPUT_CONTRADICTION

from comics.models import GenericImage

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
    # TODO: a validator for the returned crop box points

    def __init__(self, *, crop_size, **kwargs):
        self.crop_size = crop_size
        if 'widget' not in kwargs:
            kwargs['widget'] = CroppieInput()
        super().__init__(**kwargs)

    def to_python(self, data):
        f = super().to_python(data)
        if f is not None:
            # is maybe not correct to return a model field here, but
            # does make things cleaner
            return GenericImage(src=f, box=f.box, size=self.crop_size)

    def run_validators(self, value):
        super().run_validators(value and value.src)
