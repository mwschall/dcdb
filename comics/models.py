from django.db import models


class Series(models.Model):
    name = models.CharField(
        max_length=200,
    )
    slug = models.SlugField(
        allow_unicode=True,
        max_length=20,
        unique=True,
    )

    def __str__(self):
        return "%s [%s]" % (self.name, self.slug)

    class Meta:
        verbose_name_plural = "series"


class Issue(models.Model):
    series = models.ForeignKey(
        'Series',
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
    paginated = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return "%s #%s" % (self.series.name, self.number)

    class Meta:
        unique_together = ('series', 'number')


class Page(models.Model):
    issue = models.ForeignKey(
        'Issue',
        models.CASCADE,
    )
    number = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('issue', 'number')
