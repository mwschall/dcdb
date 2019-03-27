from django.core.validators import FileExtensionValidator


IMAGE_EXTS = [
    'bmp',
    'gif',
    'jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c',
    'jpg', 'jpeg', 'jpe',
    'png', 'apng',
    'tif', 'tiff',
]

ARCHIVE_EXTS = [
    'pdf',
    'zip',
]


def validate_installment_extension(value):
    return FileExtensionValidator(allowed_extensions=IMAGE_EXTS + ARCHIVE_EXTS)(value)
