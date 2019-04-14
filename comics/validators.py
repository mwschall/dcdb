from django.core.validators import FileExtensionValidator, RegexValidator

from comics.util import DEFAULT_UUID_LEN, DEFAULT_UUID_ALPHABET

IMAGE_EXTS = {
    'bmp',
    'gif',
    'jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c',
    'jpg', 'jpeg', 'jpe',
    'png', 'apng',
    'tif', 'tiff',
}

ARCHIVE_EXTS = {
    'cbz',  # 'cbt', 'cbr', 'cba', 'cb7',
    'pdf',
    'zip',
}

HANDLED_EXTS = IMAGE_EXTS | ARCHIVE_EXTS


def validate_installment_extension(value):
    return FileExtensionValidator(allowed_extensions=HANDLED_EXTS)(value)


def validate_not_suuid(value):
    regex = r'^(?![%s]{%d}\Z).*' % (DEFAULT_UUID_ALPHABET, DEFAULT_UUID_LEN)
    return RegexValidator(regex, 'Too similar to an Internal ID.')(value)
