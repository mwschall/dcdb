import math
import re
import string
import unicodedata
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

import shortuuid
from django.contrib.contenttypes.models import ContentType

VALID_FILENAME_CHARS = "-_.()#&~' %s%s" % (string.ascii_letters, string.digits)
# NOTE: allowing a few more here than is typical


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


# https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
def clean_filename(filename, whitelist=VALID_FILENAME_CHARS, replace=' ', char_limit=255):
    # replace certain chars
    if replace:
        for r in replace:
            filename = filename.replace(r, '_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)

    # truncate if requested
    if char_limit:
        if len(cleaned_filename) > char_limit:
            print("Warning, filename truncated because it was over {}. "
                  "Filenames may no longer be unique".format(char_limit))
        return cleaned_filename[:char_limit]
    return cleaned_filename


def clean_dirname(filename, whitelist=VALID_FILENAME_CHARS, replace=None, char_limit=None):
    return clean_filename(filename, whitelist=whitelist, replace=replace, char_limit=char_limit)


def get_upload_fp(data):
    if hasattr(data, 'temporary_file_path'):
        return data.temporary_file_path()
    else:
        if hasattr(data, 'read'):
            return BytesIO(data.read())
        else:
            return BytesIO(data['content'])
