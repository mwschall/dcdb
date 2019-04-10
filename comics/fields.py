from django.db import models
from django.utils.translation import gettext_lazy as _

from comics.util import s_uuid, DEFAULT_UUID_LEN


class ShortUUIDField(models.CharField):
    empty_strings_allowed = False
    description = _("Short UUID")

    def __init__(self, *args, **kwargs):
        # kwargs['blank'] = True
        if kwargs.get('max_length') is None:
            kwargs['max_length'] = DEFAULT_UUID_LEN
        super().__init__(*args, **kwargs)

    # TODO: deconstruct method?

    # noinspection PyProtectedMember
    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)

        # don't generate a value if it's not needed
        if self.primary_key and add and value is None:
            while True:
                value = s_uuid(self.max_length)
                # however rare a conflict may be, is better to go ahead and make sure here
                if not model_instance.__class__._default_manager.filter(pk=value).exists():
                    setattr(model_instance, self.attname, value)
                    break

        return value

    def formfield(self, **kwargs):
        return None


class ShortUUIDMixin(models.Model):
    id = ShortUUIDField(
        primary_key=True,
    )

    class Meta:
        abstract = True
