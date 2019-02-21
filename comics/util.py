import re

import shortuuid
from django.contrib.contenttypes.models import ContentType

DEFAULT_UUID_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_SHORTUUID = shortuuid.ShortUUID(alphabet=DEFAULT_UUID_ALPHABET)


def s_uuid(length=22):
    return DEFAULT_SHORTUUID.uuid()[:length]


def is_model_request(request, model):
    ct = ContentType.objects.get_for_model(model)
    return re.search('/{}/{}/'.format(ct.app_label, ct.model), request.path)
