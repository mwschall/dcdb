import os
import re
from io import BytesIO
from itertools import chain
from pathlib import Path

import shortuuid
from PIL import Image
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import Truncator, capfirst

from comics.fields import ShortUUIDField
from comics.util import s_uuid, unpack_numeral
from metadata.models import Credit

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


# https://timonweb.com/posts/cleanup-files-and-images-on-model-delete-in-django/
# noinspection PyBroadException, PyProtectedMember, PyUnusedLocal
def file_cleanup(sender, instance, **kwargs):
    """
    File cleanup callback used to emulate the old delete
    behavior using signals. Initially django deleted linked
    files when an object containing a File/ImageField was deleted.

    Usage:
    >>> from django.db.models.signals import post_delete
    >>> post_delete.connect(file_cleanup, sender=SourceImage, dispatch_uid="sourceimage.file_cleanup")
    """
    for field in sender._meta.get_fields():
        if field and isinstance(field, models.FileField):
            f = getattr(instance, field.name)
            m = instance.__class__._default_manager
            if hasattr(f, 'path') and os.path.exists(f.path) and \
                    not m.filter(**{'%s__exact' % field.name: f}).exclude(pk=instance.pk):
                try:
                    default_storage.delete(f.path)
                except Exception:
                    pass


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


post_delete.connect(file_cleanup, sender=GenericImage, dispatch_uid="comics.GenericImage.file_cleanup")


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


post_delete.connect(file_cleanup, sender=SourceImage, dispatch_uid="comics.SourceImage.file_cleanup")


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
        'InstallmentLabel',
        on_delete=models.PROTECT,
        default=InstallmentLabel.get_default_label,
        help_text='Numbers will be prefixed with this value when displayed.'
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
            return self.installments.select_related('page')


class Installment(ImageFileMixin, ThreadMixin, models.Model):
    # NOTE: changing these may require a DB migration
    FIRST_NUMBER = 5
    SECOND_NUMBER = 5

    series = models.ForeignKey(
        'Series',
        models.CASCADE,
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
        ordering = ['ordinal']
        unique_together = ('series', 'number', 'title')

    def __str__(self):
        return self.name

    @property
    def numeral(self):
        if self.number:
            return unpack_numeral(self.number, Installment.SECOND_NUMBER)
        return None

    @property
    def name(self):
        name = [self.series.name]
        if self.numeral is not None:
            label = self.label
            spacer = '' if re.search(r'\W$', label) else ' '
            name += [' ', label, spacer, self.numeral]
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
    def next_id(self):
        try:
            next_idx = self.ordinal  # 1-indexed, so yeah...
            return self.series.installments \
                .order_by('ordinal') \
                .values_list('pk', flat=True)[next_idx]
        except IndexError:
            return None

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
