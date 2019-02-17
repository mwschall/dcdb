from django.db import models

from comics.util import s_uuid


class ShortUUIDField(models.CharField):
    DEFAULT_LEN = 12

    def __init__(self, *args, **kwargs):
        kwargs['default'] = ShortUUIDField.gen
        kwargs['max_length'] = ShortUUIDField.DEFAULT_LEN
        super().__init__(*args, **kwargs)

    @staticmethod
    def gen():
        return s_uuid(ShortUUIDField.DEFAULT_LEN)
