from django.db.models import F
from django.db.models.query import Prefetch
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view

from comics.expressions import GroupConcat
from comics.models import Installment, Page
from metadata.models import Character, Creator


@api_view(['GET'])
def character_index(request):
    characters = Character.objects.all()
    # TODO: group by name/classification/other
    context = {
        'characters': characters,
    }
    return render(request, 'metadata/characters.html', context)


@api_view(['GET'])
def character_page(request, character):
    character = get_object_or_404(Character.objects, pk=character)
    first_pages = Page.objects.filter(order=0)
    first_issues = Installment.objects \
        .prefetch_related(Prefetch('pages', queryset=first_pages)) \
        .raw('''
        WITH    T
                AS (SELECT  ROW_NUMBER() OVER 
                                        (PARTITION BY series_id 
                                         ORDER     BY number) AS ordinal,
                            *
                    FROM    comics_installment)
        SELECT 	T.id AS id,
                series_id,
                has_cover,
                "comics_series"."name" AS series_name
        FROM   	            T   
                INNER JOIN  comics_series
                ON          comics_series.id = T.series_id
        WHERE   ordinal = 1 AND (
                T.series_id	IN (SELECT  ci0.series_id
                                FROM                comics_installment ci0
                                        INNER JOIN  metadata_appearance ma1 
                                        ON          ma1.installment_id = ci0.id
                                        INNER JOIN  metadata_persona mp0 
                                        ON          mp0.id = ma1.persona_id
                                WHERE   mp0.character_id = %s))
        ORDER  	BY "comics_series"."name"
        ''', [character.pk])

    context = {
        'character': character,
        'persona': character.primary_persona,
        'aka': ', '.join(character.aka.values_list('name', flat=True)),
        'first_issues': first_issues,
    }
    return render(request, 'metadata/character.html', context)


@api_view(['GET'])
def creator_index(request):
    # role_names = Role.objects \
    #     .filter(creators__pk=OuterRef('pk')) \
    #     .annotate(names=NAGroupConcat('name', distinct=True)) \
    #     .values('names')
    #
    # creators = Creator.objects \
    #     .annotate(role_names=Subquery(role_names)) \
    #     .iterator()

    # NOTE: gotta do a Subquery to easily sort by Role.order
    creators = Creator.objects \
        .annotate(role_names=GroupConcat(F('roles__name'), distinct=True)) \
        .iterator()

    context = {
        'creators': creators,
    }
    return render(request, 'metadata/creators.html', context)
