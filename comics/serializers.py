from rest_framework import serializers

from comics.models import Page


class PageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, instance):
        return instance.image.url if instance.image else ''

    class Meta:
        model = Page
        fields = ('image_url',)
