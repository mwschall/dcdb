from rest_framework import serializers

from comics.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('image_url',)
