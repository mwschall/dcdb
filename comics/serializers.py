from rest_framework import serializers
from rest_framework.fields import CharField

from comics.models import Page, Installment, Series


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('image_url', 'image_width', 'image_height')


class InstallmentSerializer(serializers.ModelSerializer):
    series = CharField(read_only=True)
    pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Installment
        fields = ('series', 'title', 'name', 'num_pages', 'has_cover', 'pages')


class StripInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = ('number', 'image_url', 'image_width', 'image_height')


class SeriesSerializer(serializers.ModelSerializer):
    pages = serializers.ListField(
       child=StripInstallmentSerializer()
    )

    class Meta:
        model = Series
        fields = ('name', 'pages')
