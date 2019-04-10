from django.urls.converters import StringConverter

from comics.util import DEFAULT_UUID_LEN, DEFAULT_UUID_ALPHABET


class ShortUUIDConverter(StringConverter):
    regex = '[%s]{%s}' % (DEFAULT_UUID_ALPHABET, DEFAULT_UUID_LEN)
