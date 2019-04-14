import math
import re
from decimal import Decimal, InvalidOperation
from functools import partial
from io import BytesIO
from pathlib import Path

import shortuuid
from django.contrib.contenttypes.models import ContentType
from slugify import slugify

DEFAULT_UUID_LEN = 8  # ~1 trillion with the default alphabet
DEFAULT_UUID_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_SHORTUUID = shortuuid.ShortUUID(alphabet=DEFAULT_UUID_ALPHABET)
# NOTE: changing these in Production would be... problematic


def s_uuid(length=DEFAULT_UUID_LEN):
    return DEFAULT_SHORTUUID.uuid()[:length]


# TODO: handle negatives
def pack_numeral(a, b, decimal_places):
    a = Decimal(a)
    b = Decimal(b or 0) / pow(10, decimal_places)
    return a + b


# TODO: handle negatives
def unpack_numeral(value, decimal_places, spacer='.', fmt='{}{}{}'):
    try:
        value = Decimal(value)
        a = int(math.floor(value))
        b = int(math.floor((value - a) * pow(10, decimal_places)))
        if b or fmt != '{}{}{}':
            return fmt.format(a, spacer, b)
        return str(a)
    except (InvalidOperation, TypeError):
        return None


def is_model_request(request, model):
    ct = ContentType.objects.get_for_model(model)
    return re.search('/{}/{}/'.format(ct.app_label, ct.model), request.path)


def get_ext_name(value):
    if hasattr(value, 'name'):
        value = value.name
    return Path(value).suffix[1:].lower()


def get_sort_dir(name):
    m = re.search(r'[a-z]', name, re.I)
    return m[0].upper() if m else '#'


def get_upload_fp(data):
    if hasattr(data, 'temporary_file_path'):
        return data.temporary_file_path()
    else:
        if hasattr(data, 'read'):
            return BytesIO(data.read())
        else:
            return BytesIO(data['content'])


# Would prefer awesome-slugify, but it relies on unidecode (GPL) and hasn't been
# updated in a while. Maybe just roll a combination of the two at some point...
slugify_filename = partial(slugify, max_length=250, separator='_', lowercase=False)
slugify_name = partial(slugify, lowercase=False)
