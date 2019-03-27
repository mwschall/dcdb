import math
import re
from decimal import Decimal, InvalidOperation
from io import BytesIO

import shortuuid
from django.contrib.contenttypes.models import ContentType

DEFAULT_UUID_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_SHORTUUID = shortuuid.ShortUUID(alphabet=DEFAULT_UUID_ALPHABET)


def s_uuid(length=22):
    return DEFAULT_SHORTUUID.uuid()[:length]


def unpack_numeral(value, decimal_places, spacer='.'):
    try:
        value = Decimal(value)
        a = int(math.floor(value))
        b = int(math.floor((value - a) * pow(10, decimal_places)))
        return '{}{}{}'.format(a, spacer, b) if b else str(a)
    except (InvalidOperation, TypeError):
        return None


def is_model_request(request, model):
    ct = ContentType.objects.get_for_model(model)
    return re.search('/{}/{}/'.format(ct.app_label, ct.model), request.path)


def get_upload_fp(data):
    if hasattr(data, 'temporary_file_path'):
        return data.temporary_file_path()
    else:
        if hasattr(data, 'read'):
            return BytesIO(data.read())
        else:
            return BytesIO(data['content'])
