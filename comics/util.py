import math
import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

import shortuuid
from django.contrib.contenttypes.models import ContentType

DEFAULT_UUID_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_SHORTUUID = shortuuid.ShortUUID(alphabet=DEFAULT_UUID_ALPHABET)


def s_uuid(length=22):
    return DEFAULT_SHORTUUID.uuid()[:length]


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
