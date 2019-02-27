from rest_framework import serializers

from metadata.models import Appearance, Persona


class AppearancePersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ('name',)


class PageAppearanceSerializer(serializers.ModelSerializer):
    persona = AppearancePersonaSerializer(read_only=True)

    class Meta:
        model = Appearance
        fields = ('persona', 'type', 'is_spoiler')
