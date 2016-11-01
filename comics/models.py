import os

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def generate_page_name(self, filename):
    url = "issues/{}_{}/{:03d}{}".format(
        self.issue.series.slug,
        self.issue.number,
        int(self.number),
        os.path.splitext(filename)[1]
    )
    return url


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
        return "{} [{}]".format(self.name, self.slug)

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

    def cover(self):
        return self.page_set.first().image

    def __str__(self):
        return "{} #{}".format(self.series.name, self.number)

    class Meta:
        unique_together = ('series', 'number')


class Page(models.Model):
    issue = models.ForeignKey(
        'Issue',
        models.CASCADE,
    )
    number = models.PositiveSmallIntegerField()
    image = models.ImageField(
        upload_to=generate_page_name

    )

    def __str__(self):
        return "{:03d}".format(self.number)

    class Meta:
        unique_together = ('issue', 'number')


# http://stackoverflow.com/questions/5372934/how-do-i-get-django-admin-to-delete-files-when-i-remove-an-object-from-the-datab
@receiver(post_delete, sender=Page)
def page_post_delete_handler(sender, **kwargs):
    kwargs['instance'].image.delete(save=False)
