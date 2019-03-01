from imagekit.cachefiles import ImageCacheFile
from imagekit.registry import generator_registry
from imagekit.templatetags.imagekit import parse_dimensions

DEFAULT_THUMBNAIL_GENERATOR = 'imagekit:thumbnail'


def thumbgen(*args, source=None, **kwargs):
    if len(args) == 2:
        generator_id = args[0]
        dims = args[1]
    else:
        generator_id = DEFAULT_THUMBNAIL_GENERATOR
        dims = args[0]

    dimensions = parse_dimensions(dims)
    kwargs['source'] = source
    kwargs.update(dimensions)
    generator = generator_registry.get(generator_id, **kwargs)
    return ImageCacheFile(generator)


def thumburl(*args, **kwargs):
    return thumbgen(*args, **kwargs).url
