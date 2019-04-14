import re

from django.urls.converters import StringConverter

from comics.models import Installment
from comics.util import DEFAULT_UUID_LEN, DEFAULT_UUID_ALPHABET, unpack_numeral, pack_numeral


class NumeralConverter:
    regex = r'(\d+)(?:\.(\d+))?'
    decimal_places = Installment.SECOND_NUMBER

    def to_python(self, value):
        m = re.match(self.regex, value)
        return pack_numeral(m.group(1), m.group(2), self.decimal_places)

    def to_url(self, value):
        return unpack_numeral(value, self.decimal_places)


class ShortUUIDConverter(StringConverter):
    regex = '[%s]{%s}' % (DEFAULT_UUID_ALPHABET, DEFAULT_UUID_LEN)
