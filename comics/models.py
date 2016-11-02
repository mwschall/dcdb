import os

import shortuuid
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def gen_src_loc(instance, filename):
    owner = instance.owner
    ext = os.path.splitext(filename)[1]
    if isinstance(owner, Page):
        return "installments/{}/{:04d}{}".format(
            owner.installment.slug,
            owner.order,
            ext,
        )
    else:
        return "images/{}{}".format(
            shortuuid.uuid(),
            ext,
        )


class Story(models.Model):
    name = models.CharField(
        max_length=200,
    )
    slug = models.SlugField(
        allow_unicode=True,
        max_length=20,
        unique=True,
    )

    def __str__(self):
        return "{} [{}]".format(self.name, self.slug)

    class Meta:
        verbose_name_plural = "stories"


class Installment(models.Model):
    story = models.ForeignKey(
        'Story',
        models.CASCADE
    )
    number = models.CharField(
        max_length=10,
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    has_cover = models.BooleanField(
        default=True,
    )

    @property
    def cover(self):
        return self.page_set.first().image if self.has_cover else None

    @property
    def num_pages(self):
        return self.page_set.count()

    @property
    def is_paginated(self):
        # TODO: this is stupidly inefficient
        return self.num_pages > 1

    @property
    def slug(self):
        # TODO: any way to check if number is sequential and zero-pad?
        return "{}_{}".format(self.story.slug, self.number)

    def __str__(self):
        return "{} #{}".format(self.story.name, self.number)

    class Meta:
        unique_together = ('story', 'number')
        ordering = ['story', 'number']


class Page(models.Model):
    installment = models.ForeignKey(
        'Installment',
        models.CASCADE,
    )
    order = models.PositiveSmallIntegerField(
        help_text='The 0-indexed ordering within parent Installment.',
        default=0,
        editable=False,
    )
    number = models.PositiveSmallIntegerField(
        help_text="Essentially, the page 'name'.",
    )
    images = GenericRelation(
        'SourceImage',
        related_query_name='pages',
    )

    @property
    def is_cover(self):
        # TODO: does this need to be more robust?
        return self.number == 0

    @property
    def image(self):
        return self.images.first()

    def __str__(self):
        # TODO: keep number or use order?
        return "{}".format(self.number)

    class Meta:
        # NOTE: don't add order to uniqueness constraint (See: goo.gl/nnctw0)
        ordering = ['order']


class SourceImage(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey()

    file = models.ImageField(
        upload_to=gen_src_loc
    )
    # TODO: do we /really/ care about this?
    # http://stackoverflow.com/questions/4892729/
    original_name = models.CharField(
        max_length=260
    )

    @property
    def url(self):
        return self.file.url

    class Meta:
        unique_together = ('content_type', 'object_id')


# http://stackoverflow.com/questions/5372934/
@receiver(post_delete, sender=SourceImage)
def image_post_delete_handler(sender, **kwargs):
    kwargs['instance'].file.delete(save=False)
