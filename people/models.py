from urllib.parse import urlparse

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import capfirst


class Entity(models.Model):
    working_name = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        ordering = ['working_name']
        verbose_name_plural = 'entities'

    def __str__(self):
        return self.working_name

    def clean(self):
        # Note: DO NOT destroy inner white spacing as a matter of courtesy.
        self.working_name = self.working_name.strip()


class EntityUrl(models.Model):
    entity = models.ForeignKey(
        'Entity',
        related_name='urls',
        on_delete=models.CASCADE,
    )
    link = models.URLField()
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'url'

    def __str__(self):
        return urlparse(self.link).hostname


class Role(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    # TODO: 'importance' metric as opposed to strict 'order'?

    class Meta:
        ordering = ['name']

    def __str__(self):
        return capfirst(self.name)

    def clean(self):
        self.name = ' '.join(self.name.split()).lower()


class Credit(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    entity = models.ForeignKey(
        Entity,
        models.CASCADE,
    )
    role = models.ForeignKey(
        Role,
        models.CASCADE,
    )

    class Meta:
        # TODO: This doesn't fail gracefully.
        unique_together = ('object_id', 'content_type', 'entity', 'role')

    def __str__(self):
        return '%s [%s]' % (self.entity, self.role)

    def __hash__(self):
        return hash((self.entity, self.role))
