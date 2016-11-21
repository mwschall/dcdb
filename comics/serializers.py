from rest_framework import serializers
from rest_framework.fields import CharField

from comics.models import Page, Installment


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('image_url', 'image_width', 'image_height')


class InstallmentSerializer(serializers.ModelSerializer):
    series = CharField(read_only=True)
    pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Installment
        fields = ('series', 'title', 'num_pages', 'has_cover', 'pages')
