from rest_framework import serializers
from rest_framework.fields import CharField

from comics.models import Page, Installment, Series
from metadata.serializers import PageAppearanceSerializer

PAGE_FIELDS = ('image_url', 'image_width', 'image_height',)
THREAD_FIELDS = ('name', 'num_pages', 'pages',)


class PageSerializer(serializers.ModelSerializer):
    appearances = PageAppearanceSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = PAGE_FIELDS + ('appearances',)


class InstallmentSerializer(serializers.ModelSerializer):
    series = CharField(read_only=True)
    pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Installment
        fields = THREAD_FIELDS + ('series', 'title', 'synopsis', 'has_cover',)


class StripInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = PAGE_FIELDS + ('number', 'title', 'synopsis',)


class SeriesSerializer(serializers.ModelSerializer):
    pages = StripInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = Series
        fields = THREAD_FIELDS
