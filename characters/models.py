from urllib.parse import urlparse

from django.db import models
from django.db.models import F
from django.utils.text import capfirst

from people.models import Entity

GIVEN_NAME = 'GN'
SUPER_IDENTITY = 'SI'
ALIAS = 'JJ'
PERSONA_TYPE_CHOICES = (
    # NOTE: multiple Given Names are allowed (see: Superman)
    (GIVEN_NAME, 'Given Name'),
    (SUPER_IDENTITY, 'Super Identity'),
    (ALIAS, 'Alias'),
    # TODO: probably need a few more for good measure, but what?
)

NORMAL = 'N'
OFF_SCREEN = 'O'
MENTIONED = 'M'
CAMEO = 'C'
SPOILER = 'S'
APPEARANCE_TYPE_CHOICES = (
    (NORMAL, 'Normal'),
    (OFF_SCREEN, 'Off Screen'),
    (MENTIONED, 'Mentioned'),
    # TODO: Not sure if this option is necessary or proper...
    (CAMEO, 'Cameo'),
)


class Classification(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return capfirst(self.name)

    def clean(self):
        self.name = ' '.join(self.name.split()).lower()


class Being(models.Model):
    primary_persona = models.OneToOneField(
        'Persona',
        related_name='primary_for',
        # TODO: this should NEVER be null, but allowing it makes writing the admin site easier
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    bio = models.TextField(
        blank=True,
    )

    @property
    def name(self):
        return str(self)

    @property
    def aka(self):
        return self.personas.exclude(pk=self.primary_persona.pk)

    @property
    def creators(self):
        return Entity.objects.filter(persona__being=self).distinct()

    class Meta:
        ordering = ['primary_persona__name']

    def __str__(self):
        primary = self.primary_persona
        return primary.name if primary else '(New)'


class BeingUrl(models.Model):
    being = models.ForeignKey(
        'Being',
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


class PersonaDisplayManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() \
            .annotate(cls_name=F('classification__name'))


class Persona(models.Model):
    being = models.ForeignKey(
        'Being',
        related_name='personas',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=200,
    )
    type = models.CharField(
        max_length=2,
        choices=PERSONA_TYPE_CHOICES,
        default=GIVEN_NAME,
    )
    classification = models.ForeignKey(
        'Classification',
        related_name='characters',
        on_delete=models.PROTECT,
        default=1,
    )
    mug_shot = models.ManyToManyField(
        'comics.SourceImage',
        through='MugShot',
        related_name='mug_shots_for',
        blank=True,
    )
    profile_pic = models.OneToOneField(
        'comics.SourceImage',
        related_name='profile_of',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    creators = models.ManyToManyField(
        'people.Entity',
        related_name='characters',
        related_query_name='persona',
        blank=True,
    )

    appearances = models.ManyToManyField(
        'comics.Page',
        through='Appearance',
        related_name='characters',
    )

    @property
    def is_primary(self):
        if not hasattr(self, '_is_primary'):
            try:
                self._is_primary = self.being.primary_persona == self
            except Being.DoesNotExist:
                self.is_primary = False
        return self._is_primary

    @is_primary.setter
    def is_primary(self, value):
        self._is_primary = value

    @property
    def aka(self):
        return self.being.personas.exclude(pk=self.pk)

    @property
    def cls_name(self):
        if not hasattr(self, '_cls_name'):
            self._cls_name = self.classification.name
        return capfirst(self._cls_name)

    @cls_name.setter
    def cls_name(self, value):
        self._cls_name = value

    objects = models.Manager()
    display_objects = PersonaDisplayManager()

    class Meta:
        ordering = ['name']
        unique_together = ('being', 'name')
        default_manager_name = 'display_objects'

    def __str__(self):
        return self.name

    def clean(self):
        # NOTE: Minimal cleaning is desirable and proper. Or is it?
        self.name = self.name.strip()


class MugShot(models.Model):
    persona = models.ForeignKey(
        'Persona',
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        'comics.SourceImage',
        on_delete=models.PROTECT,
    )
    center_x = models.FloatField()
    center_y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()


class Appearance(models.Model):
    persona = models.ForeignKey(
        'Persona',
        # TODO: this should really be PROTECT, but using CASCADE during initial development
        on_delete=models.CASCADE,
    )
    installment = models.ForeignKey(
        'comics.Installment',
        on_delete=models.CASCADE,
        related_name='appearances',
    )
    page = models.ForeignKey(
        'comics.Page',
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=1,
        choices=APPEARANCE_TYPE_CHOICES,
        default=NORMAL,
    )
    is_spoiler = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['page__order']
        # mostly looking up by Installment, yes?
        unique_together = ('installment', 'persona', 'page')

    def __str__(self):
        return '{} in {} at [{}]'.format(self.persona, self.installment, self.page.order)
