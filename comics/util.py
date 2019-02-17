import shortuuid

DEFAULT_UUID_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_SHORTUUID = shortuuid.ShortUUID(alphabet=DEFAULT_UUID_ALPHABET)


def s_uuid(length=22):
    return DEFAULT_SHORTUUID.uuid()[:length]
