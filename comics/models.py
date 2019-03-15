import os
import re
from io import BytesIO
from itertools import chain
from pathlib import Path

import shortuuid
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import Q, OuterRef
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator, capfirst

from comics.expressions import SQCount
from comics.fields import ShortUUIDField
from comics.util import s_uuid, unpack_numeral

#########################################
# Defines                               #
#########################################

LTR = 'LTR'
RTL = 'RTL'
FLIP_DIRECTION_CHOICES = (
    (LTR, 'Left-to-Right'),
    (RTL, 'Right-to-Left'),
)

FREEFORM = 'F'
STORY = 'S'
VOLUME = 'V'
ARC = 'A'
THREAD_TYPE_CHOICES = (
    (FREEFORM, 'Freeform'),
    (STORY, 'Story'),
    (VOLUME, 'Volume'),
    (ARC, 'Arc'),
)


#########################################
# Utility Methods                       #
#########################################

def get_ci_loc(instance, filename):
    return "profiles/{}{}".format(instance.id, Path(filename).suffix)


def get_ci_src_loc(instance, filename):
    # ghetto security precaution:
    # tack on a random string to prevent people getting at the source for a cropped image
    return "raws/{}-{}{}".format(instance.id, s_uuid(), Path(filename).suffix)


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


#########################################
# Images                                #
#########################################


class ImageFileMixin(object):
    @property
    def image_url(self):
        return self.safe_file.url

    @property
    def image_width(self):
        return self.safe_file.width

    @property
    def image_height(self):
        return self.safe_file.height


class GenericImage(ImageFileMixin, models.Model):
    id = ShortUUIDField(primary_key=True)
    scaled = models.ImageField(
        upload_to=get_ci_loc,
        width_field='scaled_width',
        height_field='scaled_height',
    )
    scaled_width = models.PositiveIntegerField()
    scaled_height = models.PositiveIntegerField()

    # NOTE: src is actually the core of this class; could ditch the scaled field
    #       for some on-demand generation system in the future
    src = models.ImageField(
        upload_to=get_ci_src_loc,
    )
    # define a standard box, but final display can be as a rectangle OR oval
    x1 = models.PositiveIntegerField(default=0)
    y1 = models.PositiveIntegerField(default=0)
    x2 = models.PositiveIntegerField(default=0)
    y2 = models.PositiveIntegerField(default=0)

    # TODO: corresponding cleanup task
    is_deleted = models.BooleanField(default=False)

    @property
    def box(self):
        if self.x2 > self.x1 and self.y2 > self.y1:
            return self.x1, self.y1, self.x2, self.y2
        return None

    @box.setter
    def box(self, value):
        self.x1 = value[0]
        self.y1 = value[1]
        self.x2 = value[2]
        self.y2 = value[3]

    @property
    def size(self):
        if self.scaled_width and self.scaled_height:
            return self.scaled_width, self.scaled_height
        return None

    @size.setter
    def size(self, value):
        self.scaled_width = value[0]
        self.scaled_height = value[1]

    @property
    def safe_file(self):
        return self.scaled

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.src is not None and self.box is None:
            image = getattr(self.src, 'image', None)
            if image:
                self.box = (0, 0, image.width, image.height)


# noinspection PyUnusedLocal
@receiver(pre_save, sender=GenericImage)
def scaled_img_pre_save_handler(sender, instance, **kwargs):
    if instance.scaled:
        return

    buf = BytesIO()
    # can't use instance.src(.file).image for some reason, so have to reopen
    with Image.open(instance.src.file) as src:
        try:
            crop = src.resize(instance.size, Image.LANCZOS, instance.box)
        except TypeError:
            crop = src.crop(instance.box)
        crop.save(buf, 'PNG', optimize=True)

    # TODO: support output in other formats
    instance.scaled = InMemoryUploadedFile(buf, None, 'crop.png', 'image/png', buf.tell(), None)


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
    def safe_file(self):
        return self.file


#########################################
# Series & Installments                 #
#########################################

class InstallmentLabel(models.Model):
    value = models.CharField(
        max_length=50,
        unique=True,
    )

    class Meta:
        ordering = ['value']

    def __str__(self):
        return self.display_value

    @property
    def display_value(self):
        return capfirst(self.value)

    def save(self, *args, **kwargs):
        # perform some basic normalization
        self.value = re.sub(r'\s+', ' ', self.value).strip().lower()
        super().save(*args, **kwargs)

    @staticmethod
    def get_default_label():
        return InstallmentLabel.objects.first()


class ThreadMixin(object):
    @property
    def num_pages(self):
        return self.pages.count()


class SeriesDisplayManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() \
            .annotate(installment_count=Series.installment_count_sq())


class Series(ThreadMixin, models.Model):
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
    installment_label = models.ForeignKey(
        'comics.InstallmentLabel',
        on_delete=models.PROTECT,
        default=InstallmentLabel.get_default_label,
        help_text='Numbers will be prefixed with this value when displayed.'
    )
    flip_direction = models.CharField(
        max_length=3,
        choices=FLIP_DIRECTION_CHOICES,
        default=LTR,
    )

    @property
    def first_cover(self):
        return self.installments.first().cover

    @property
    def latest_cover(self):
        return self.installments.last().cover

    objects = models.Manager()
    display_objects = SeriesDisplayManager()

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return "{} [{}]".format(self.name, self.slug)

    def get_absolute_url(self):
        if self.is_strip:
            return reverse('comics:strip', args=[self.pk])
        return reverse('comics:series', args=[self.pk])

    @property
    def pages(self):
        if self.is_strip:
            return self.installments.select_related('page')

    @staticmethod
    def installment_count_sq():
        return SQCount(Installment.objects
                       .order_by()
                       .filter(series=OuterRef('pk'))
                       .values('pk')
                       )


class Installment(ImageFileMixin, ThreadMixin, models.Model):
    # NOTE: changing these may require a DB migration
    FIRST_NUMBER = 5
    SECOND_NUMBER = 5

    series = models.ForeignKey(
        'comics.Series',
        on_delete=models.CASCADE,
        related_name='installments',
    )
    ordinal = models.PositiveIntegerField(
        default=0,
        help_text='1-indexed default ordering within containing Series.',
    )
    number = models.DecimalField(
        max_digits=FIRST_NUMBER + SECOND_NUMBER,
        decimal_places=SECOND_NUMBER,
        blank=True,
        null=True,
        help_text='Numeric designation, not including common label.',
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='In place of, or in addition to, a Number.'
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
        'comics.Page',
        on_delete=models.SET_NULL,
        related_name='strip',
        null=True,
        editable=False,
    )

    class Meta:
        ordering = ['ordinal']
        unique_together = ('series', 'number', 'title')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('comics:installment', args=[self.pk])

    @property
    def numeral(self):
        if self.number:
            return unpack_numeral(self.number, Installment.SECOND_NUMBER)
        return None

    @property
    def display_number(self):
        if self.numeral is not None:
            if re.search(r'\W$', self.label):
                tmpl = 'Issue {}{}'
            else:
                tmpl = '{} {}'
            return tmpl.format(self.label, self.numeral)

    @property
    def name(self):
        name = [self.series.name]
        if self.numeral is not None:
            spacer = '' if re.search(r'\W$', self.label) else ' '
            name += [' ', self.label, spacer, self.numeral]
        if self.title:
            name += [' — ', self.title]
        return ''.join(name)

    @property
    def label(self):
        return self.series.installment_label.display_value

    @property
    def cover(self):
        return self.pages.first() if self.has_cover else None

    @property
    def is_paginated(self):
        # TODO: this is stupidly inefficient
        return self.num_pages > 1

    @property
    def slug(self):
        # TODO: this is SUPER busted and needs to depend on stable values
        return "{}_{}".format(self.series.slug, self.ordinal)

    @property
    def prev_id(self):
        if not hasattr(self, '_prev_id'):
            try:
                prev_idx = self.ordinal - 2  # 1-indexed, so yeah...
                self._prev_id = self.series.installments \
                    .order_by('ordinal') \
                    .values_list('pk', flat=True)[prev_idx]
            except (AssertionError, IndexError):
                self._prev_id = None
        return self._prev_id

    @prev_id.setter
    def prev_id(self, value):
        self._prev_id = value

    @property
    def next_id(self):
        # TODO: use a LEAD() window function in certain circumstances?
        if not hasattr(self, '_next_id'):
            try:
                next_idx = self.ordinal  # 1-indexed, so yeah...
                self._next_id = self.series.installments \
                    .order_by('ordinal') \
                    .values_list('pk', flat=True)[next_idx]
            except IndexError:
                self._next_id = None
        return self._next_id

    @next_id.setter
    def next_id(self, value):
        self._next_id = value

    @property
    def page_count(self):
        if not hasattr(self, '_pc'):
            self._pc = self.pages.count()
        return self._pc

    @page_count.setter
    def page_count(self, value):
        self._pc = value

    @property
    def safe_file(self):
        return self.page.file


class Page(SourceImage):
    installment = models.ForeignKey(
        'comics.Installment',
        on_delete=models.CASCADE,
        related_name='pages',
    )
    order = models.PositiveSmallIntegerField(
        help_text='The 0-indexed ordering within parent Installment.',
        default=0,
        editable=False,
    )

    class Meta:
        # NOTE: don't add order to uniqueness constraint (See: goo.gl/nnctw0)
        ordering = ['order']

    def __str__(self):
        return "{}".format(self.order)

    def get_absolute_url(self):
        return reverse('comics:page', args=[self.installment_id, self.order])

    @property
    def is_cover(self):
        return self.order is 0 and self.installment.has_cover

    @property
    def number(self):
        return self.order if self.installment.has_cover else self.order + 1


#########################################
# Threads                               #
#########################################

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
        'comics.Installment',
        through='comics.ThreadSequence',
    )

    def __str__(self):
        trunc = Truncator(self.name)
        return trunc.words(4)

    def get_absolute_url(self):
        return reverse('comics:thread', args=[self.pk])

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
        'comics.Thread',
        on_delete=models.CASCADE,
    )
    order = models.PositiveSmallIntegerField(
        default=0,
    )
    installment = models.ForeignKey(
        'comics.Installment',
        on_delete=models.PROTECT,
    )
    # TODO: make these ForeignKeys for a number of reasons
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
