import os
from itertools import chain

import shortuuid
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import Truncator

from people.models import Credit

LTR = 'LTR'
RTL = 'RTL'
FLIP_DIRECTION_CHOICES = (
    (LTR, 'Left-to-Right'),
    (RTL, 'Right-to-Left'),
)

FREEFORM = 'F'
STORY = 'S'
VOLUME = 'V',
ARC = 'A',
THREAD_TYPE_CHOICES = (
    (FREEFORM, 'Freeform'),
    (STORY, 'Story'),
    (VOLUME, 'Volume'),
    (ARC, 'Arc'),
)


# TODO: ra ra efficiency, either prefetch_related or merge in DB
def get_full_credits(m):
    credit_set = set()

    if isinstance(m, Page):
        credit_set = credit_set | set(m.credits.all())
        m = m.installment
    if isinstance(m, Installment):
        credit_set = credit_set | set(m.credits.all())
        m = m.series
    if isinstance(m, Series):
        credit_set = credit_set | set(m.credits.all())

    return list(credit_set)


# TODO: put this in the subclasses of SourceImage
def gen_src_loc(instance, filename):
    ext = os.path.splitext(filename)[1]
    if isinstance(instance, Page):
        return "installments/{}/{:04d}{}".format(
            instance.installment.slug,
            instance.order,
            ext,
        )
    else:
        return "images/{}{}".format(
            shortuuid.uuid(),
            ext,
        )


class ImageFileMixin(object):
    @property
    def safe_file(self):
        try:
            return self.file
        except AttributeError:
            return self.page.file

    @property
    def image_url(self):
        return self.safe_file.url

    @property
    def image_width(self):
        return self.safe_file.width

    @property
    def image_height(self):
        return self.safe_file.height


class Series(models.Model):
    name = models.CharField(
        max_length=200,
    )
    slug = models.SlugField(
        allow_unicode=True,
        max_length=20,
        unique=True,
    )
    is_strip = models.BooleanField(
        default=False,
    )
    flip_direction = models.CharField(
        max_length=3,
        choices=FLIP_DIRECTION_CHOICES,
        default=LTR,
    )
    credits = GenericRelation(
        Credit,
        related_query_name='series',
    )

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return "{} [{}]".format(self.name, self.slug)

    @property
    def pages(self):
        if self.is_strip:
            return self.installments.select_related('page').order_by('release_datetime')


class Installment(ImageFileMixin, models.Model):
    series = models.ForeignKey(
        'Series',
        models.CASCADE,
        related_name='installments',
    )
    number = models.CharField(
        max_length=10,
    )
    title = models.CharField(
        max_length=200,
        blank=True,
    )
    synopsis = models.TextField(
        blank=True,
    )
    release_datetime = models.DateTimeField(
        default=timezone.now
    )
    has_cover = models.BooleanField(
        default=True,
    )
    page = models.OneToOneField(
        'Page',
        models.SET_NULL,
        related_name='strip',
        null=True,
        editable=False,
    )
    credits = GenericRelation(
        Credit,
        related_query_name='installments',
    )

    class Meta:
        unique_together = ('series', 'number')
        ordering = ['series', 'number']

    def __str__(self):
        return self.name

    @property
    def name(self):
        return "{} #{}".format(self.series.name, self.number)

    @property
    def cover(self):
        return self.pages.first() if self.has_cover else None

    @property
    def num_pages(self):
        return self.pages.count()

    @property
    def is_paginated(self):
        # TODO: this is stupidly inefficient
        return self.num_pages > 1

    @property
    def slug(self):
        # TODO: any way to check if number is sequential and zero-pad?
        return "{}_{}".format(self.series.slug, self.number)


class SourceImage(ImageFileMixin, models.Model):
    file = models.ImageField(
        upload_to=gen_src_loc,
        width_field='file_width',
        height_field='file_height',
    )
    file_width = models.PositiveIntegerField()
    file_height = models.PositiveIntegerField()
    # TODO: do we /really/ care about this?
    # http://stackoverflow.com/questions/4892729/
    original_name = models.CharField(
        max_length=260,
    )

    @property
    def url(self):
        return self.file.url


# http://stackoverflow.com/questions/5372934/
@receiver(post_delete, sender=SourceImage)
def image_post_delete_handler(sender, **kwargs):
    kwargs['instance'].file.delete(save=False)


class Page(SourceImage):
    installment = models.ForeignKey(
        'Installment',
        models.CASCADE,
        related_name='pages',
    )
    order = models.PositiveSmallIntegerField(
        help_text='The 0-indexed ordering within parent Installment.',
        default=0,
        editable=False,
    )
    credits = GenericRelation(
        Credit,
        related_query_name='pages',
    )

    class Meta:
        # NOTE: don't add order to uniqueness constraint (See: goo.gl/nnctw0)
        ordering = ['order']

    def __str__(self):
        return "{}".format(self.order)

    @property
    def is_cover(self):
        return self.order is 0 and self.installment.has_cover

    @property
    def number(self):
        return self.order if self.installment.has_cover else self.order + 1


class Thread(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
    )
    synopsis = models.TextField(
        blank=True,
    )
    type = models.CharField(
        max_length=1,
        choices=THREAD_TYPE_CHOICES,
        default=FREEFORM,
    )
    issue_based = models.BooleanField(
        default=False,
    )
    installments = models.ManyToManyField(
        'Installment',
        through='ThreadSequence',
    )

    def __str__(self):
        trunc = Truncator(self.name)
        return trunc.words(4)

    @property
    def cover(self):
        return self.threadsequence_set.first().first_page

    @property
    def pages(self):
        pages = chain()
        for ts in self.threadsequence_set.iterator():
            pages = chain(pages, ts.pages)
        return list(pages)


class ThreadSequence(models.Model):
    thread = models.ForeignKey(
        'Thread',
        models.CASCADE,
    )
    order = models.PositiveSmallIntegerField(
        default=0,
    )
    installment = models.ForeignKey(
        'Installment',
        models.PROTECT,
    )
    begin_page = models.PositiveSmallIntegerField(
        default=0,
    )
    end_page = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['order']

    @property
    def first_page(self):
        return Page.objects.get(
            Q(installment=self.installment),
            Q(order=self.begin_page),
        )

    @property
    def pages(self):
        if self.end_page:
            return Page.objects.filter(
                Q(installment=self.installment),
                Q(order__range=(self.begin_page, self.end_page)),
            )
        else:
            return Page.objects.filter(
                Q(installment=self.installment),
                Q(order__gte=self.begin_page),
            )
