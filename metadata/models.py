from operator import itemgetter
from urllib.parse import urlparse

from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from tldextract import extract as urlextract

#########################################
# Defines                               #
#########################################

GIVEN_NAME = 'GN'
SUPER_IDENTITY = 'SI'
PERSONALITY = 'AP'
TITLE = 'TL'
ALIAS = 'JJ'
ROLE = 'RP'
PERSONA_TYPE_CHOICES = (
    # NOTE: multiple Given Names are allowed (see: Superman)
    (GIVEN_NAME, 'Given Name'),
    (SUPER_IDENTITY, 'Super Identity'),
    (PERSONALITY, 'Personality'),
    (TITLE, 'Title'),
    (ALIAS, 'Alias'),
    (ROLE, 'Role')
)

# NOTE: these feel comprehensive, but there might be one more
STANDARD = 'S'
OFF_SCREEN = 'O'
MENTIONED = 'M'
APPEARANCE_TYPE_CHOICES = (
    (STANDARD, 'Standard'),
    (OFF_SCREEN, 'Off Screen'),
    (MENTIONED, 'Mentioned'),
)

# https://fontawesome.com/icons?d=gallery&s=brands
DOMAIN_ICON_MAP = {
    'blogger': 'blogger-b',
    'blogspot': 'blogger-b',
    'deviantart': 'deviantart',
    'facebook': 'facebook',
    'flickr': 'flickr',
    'instagram': 'instagram',
    'patreon': 'patreon',
    'tumblr': 'tumblr',
    'twitter': 'twitter',
}


#########################################
# Creators and Roles                    #
#########################################

class Creator(models.Model):
    working_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Name of person/group/collective/circle/etc.'
    )
    # TODO: sort_name field?
    avatar = models.ImageField(
        upload_to='avatars',
        blank=True,
    )

    works = models.ManyToManyField(
        'comics.Installment',
        through='metadata.Credit',
        related_name='creators',
    )

    roles = models.ManyToManyField(
        'metadata.Role',
        through='metadata.Credit',
        related_name='creators',
    )

    @cached_property
    def social_urls(self):
        urls = [{'href': u.link, 'icon': u.icon_name}
                for u in self.urls.all() if u.icon_name]
        return sorted(urls, key=itemgetter('icon'))

    @cached_property
    def websites(self):
        return [{'href': u.link, 'name': str(u)}
                for u in self.urls.all() if not u.icon_name]

    class Meta:
        ordering = ['working_name']
        verbose_name_plural = 'creators'

    def __str__(self):
        return self.working_name

    def clean(self):
        # Note: DO NOT destroy inner white spacing as a matter of courtesy.
        self.working_name = self.working_name.strip()


class CreatorUrl(models.Model):
    creator = models.ForeignKey(
        'metadata.Creator',
        related_name='urls',
        on_delete=models.CASCADE,
    )
    link = models.URLField()
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Preferred display order.'
    )

    @cached_property
    def icon_name(self):
        domain = urlextract(self.link).domain.lower()
        return DOMAIN_ICON_MAP.get(domain)

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
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Default order to list different role types.'
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return capfirst(self.name)

    def clean(self):
        self.name = ' '.join(self.name.split()).lower()


class Credit(models.Model):
    installment = models.ForeignKey(
        'comics.Installment',
        related_name='credits',
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        'metadata.Creator',
        related_name='credits',
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        'metadata.Role',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['role__order', 'creator__working_name']
        unique_together = ('installment', 'role', 'creator')

    def __str__(self):
        return '%s [%s]' % (self.creator, self.role)

    def __hash__(self):
        return hash((self.creator, self.role))


#########################################
# Characters & Personas                 #
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


class Character(models.Model):
    primary_persona = models.OneToOneField(
        'metadata.Persona',
        related_name='primary_for',
        # NOTE: should NEVER be null, but practically speaking it has to be enforced in business logic
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='What this character is primarily known as.',
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
        return Creator.objects.filter(persona__character=self).distinct()

    @property
    def mugshot(self):
        primary = self.primary_persona
        return primary.mugshot if primary else None

    class Meta:
        ordering = ['primary_persona__name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('metadata:character', args=[self.pk])


class CharacterUrl(models.Model):
    character = models.ForeignKey(
        'metadata.Character',
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
    character = models.ForeignKey(
        'metadata.Character',
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
        'metadata.Classification',
        related_name='personas',
        on_delete=models.PROTECT,
        default=1,
        help_text='Alter ego manner of being. (See: Shazam)',
    )
    mugshot = models.ImageField(
        upload_to='personas',
        blank=True,
    )
    profile_pic = models.ImageField(
        upload_to='personas',
        blank=True,
    )

    creators = models.ManyToManyField(
        'metadata.Creator',
        related_name='personas',
        related_query_name='persona',
        blank=True,
    )

    installments = models.ManyToManyField(
        'comics.Installment',
        through='metadata.Appearance',
        related_name='personas',
    )
    pages = models.ManyToManyField(
        'comics.Page',
        through='metadata.Appearance',
        related_name='personas',
    )

    @property
    def is_primary(self):
        if not hasattr(self, '_is_primary'):
            try:
                self._is_primary = self.character.primary_persona == self
            except Character.DoesNotExist:
                self.is_primary = False
        return self._is_primary

    @is_primary.setter
    def is_primary(self, value):
        self._is_primary = value

    @property
    def aka(self):
        return self.character.personas.exclude(pk=self.pk)

    @property
    def cls_name(self):
        if not hasattr(self, '_cls_name'):
            self._cls_name = self.classification.name
        return capfirst(self._cls_name)

    @cls_name.setter
    def cls_name(self, value):
        self._cls_name = value

    @property
    def avatar(self):
        return self.mugshot

    objects = models.Manager()
    display_objects = PersonaDisplayManager()

    class Meta:
        ordering = ['name']
        unique_together = ('character', 'name')
        default_manager_name = 'display_objects'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('metadata:character', args=[self.character_id])

    def clean(self):
        # NOTE: Minimal cleaning is desirable and proper. Or is it?
        self.name = self.name.strip()


class Appearance(models.Model):
    persona = models.ForeignKey(
        'metadata.Persona',
        # TODO: PROTECT may be better, but using CASCADE during initial development
        on_delete=models.CASCADE,
        related_name='appearances',
    )
    installment = models.ForeignKey(
        'comics.Installment',
        on_delete=models.CASCADE,
        related_name='appearances',
    )
    page = models.ForeignKey(
        'comics.Page',
        on_delete=models.CASCADE,
        related_name='appearances',
    )
    type = models.CharField(
        max_length=1,
        choices=APPEARANCE_TYPE_CHOICES,
        default=STANDARD,
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
