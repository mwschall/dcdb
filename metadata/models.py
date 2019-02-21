from urllib.parse import urlparse

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import F
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.text import capfirst

#########################################
# Defines                               #
#########################################

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

PROFILE = 'P'
MUGSHOT = 'M'
PERSONA_IMAGE_TYPE_CHOICES = (
    (PROFILE, 'Profile'),
    (MUGSHOT, 'Mugshot'),
)

NORMAL = 'N'
OFF_SCREEN = 'O'
MENTIONED = 'M'
APPEARANCE_TYPE_CHOICES = (
    (NORMAL, 'Normal'),
    (OFF_SCREEN, 'Off Screen'),
    (MENTIONED, 'Mentioned'),
)


#########################################
# People                                #
#########################################

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
    order = models.PositiveSmallIntegerField(default=0)

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


#########################################
# Beings & Personas                     #
#########################################

class Classification(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    order = models.PositiveSmallIntegerField(default=0)

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
        # NOTE: should NEVER be null, but practically speaking it has to be enforced in business logic
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='What this being is primarily known as.',
    )
    bio = models.TextField(
        blank=True,
        help_text='One-to-several paragraphs, but not a full wiki entry.',
    )

    @property
    def name(self):
        primary = self.primary_persona
        return primary.name if primary else '(New)'

    @property
    def aka(self):
        return self.personas.exclude(pk=self.primary_persona.pk)

    @property
    def creators(self):
        return Entity.objects.filter(persona__being=self).distinct()

    @property
    def mugshot(self):
        primary = self.primary_persona
        return primary.mugshot if primary else None

    class Meta:
        ordering = ['primary_persona__name']

    def __str__(self):
        return self.name


class BeingUrl(models.Model):
    being = models.ForeignKey(
        'Being',
        related_name='urls',
        on_delete=models.CASCADE,
    )
    link = models.URLField()
    order = models.PositiveSmallIntegerField(default=0)

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
        blank=True,
        help_text='Singular underlying entity.',
    )
    name = models.CharField(
        max_length=200,
        help_text='Full name, without any additional designation.',
    )
    type = models.CharField(
        max_length=2,
        choices=PERSONA_TYPE_CHOICES,
        default=GIVEN_NAME,
        help_text='Alter ego type or purpose.',
    )
    classification = models.ForeignKey(
        'Classification',
        related_name='characters',
        on_delete=models.PROTECT,
        default=1,
        help_text='Alter ego manner of being. (See: Shazam)',
    )
    images = models.ManyToManyField(
        'comics.GenericImage',
        through='PersonaImage',
        related_query_name='personas',
        blank=True,
    )

    creators = models.ManyToManyField(
        'Entity',
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

    @property
    def mugshot(self):
        try:
            return self.images.filter(personaimage__type=MUGSHOT).first()
        except ValueError:
            return None

    @mugshot.setter
    @transaction.atomic
    def mugshot(self, value):
        current = self.mugshot
        if value is current:
            return
        if current:
            self.images \
                .filter(personaimage__type=MUGSHOT) \
                .update(is_deleted=True)
            PersonaImage.objects \
                .filter(persona=self, type=MUGSHOT) \
                .all().delete()
        if value:
            value.save()
            pi = PersonaImage(persona=self, image=value, type=MUGSHOT)
            pi.save()

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


# noinspection PyUnusedLocal
@receiver(pre_delete, sender=Persona)
def persona_images_delete_handler(sender, instance, **kwargs):
    # flag is to prevent data loss should an error occur somewhere in a post_delete change
    instance.images.update(is_deleted=True)


class PersonaImage(models.Model):
    persona = models.ForeignKey(
        'Persona',
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(
        'comics.GenericImage',
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=1,
        choices=PERSONA_IMAGE_TYPE_CHOICES,
        default=PROFILE,
    )


class Appearance(models.Model):
    persona = models.ForeignKey(
        'Persona',
        # TODO: PROTECT may be better, but using CASCADE during initial development
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
        help_text='Whether visible on the page, or otherwise present.',
    )
    is_spoiler = models.BooleanField(
        default=False,
        help_text='Obscure this appearance in certain contexts.',
    )

    class Meta:
        ordering = ['page__order']
        # mostly looking up by Installment, yes?
        unique_together = ('installment', 'persona', 'page')

    def __str__(self):
        # NOTE: begin/end_ord are the currently informal definition of a range
        ordinal = self.begin_ord if hasattr(self, 'begin_ord') else self.page.order
        return '{} in {} at [{}]'.format(self.persona, self.installment, ordinal)