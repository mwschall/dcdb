from django.db.models import F, Exists, OuterRef, Q, Count
from django.db.models.query import Prefetch
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view

from comics.expressions import GroupConcat
from comics.models import Installment, Page, Series
from metadata.models import Character, Creator, Persona


@api_view(['GET'])
def character_index(request):
    characters = Character.objects \
        .select_related('primary_persona') \
        .all()

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
        WHERE   T.ordinal = 1 AND (
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
    # NOTE: gotta do a Subquery to easily sort by Role.order
    creators = Creator.objects \
        .annotate(role_names=GroupConcat(F('roles__name'), distinct=True)) \
        .iterator()

    context = {
        'creators': creators,
    }
    return render(request, 'metadata/creators.html', context)


@api_view(['GET'])
def creator_page(request, creator):
    creator = get_object_or_404(Creator, id=creator)

    # show only primary if is created by, else list each Persona individually
    characters = Persona.objects \
        .annotate(is_primary=Exists(Character.objects.filter(primary_persona=OuterRef('pk'))),
                  has_primary=Exists(Character.objects.filter(primary_persona__creators__pk=creator.pk,
                                                              pk=OuterRef('character_id')))) \
        .filter(Q(is_primary=True) | Q(has_primary=False),
                creators__pk=creator.pk) \
        .only('name', 'mugshot', 'character_id') \
        .iterator()

    # return one row per role and perform a groupby in the template rendering
    series = Series.display_objects \
        .filter(installments__creators__pk=creator.pk) \
        .annotate(role_name=F('installments__credits__role__name'),
                  role_count=Count(F('installments__credits__role__name'))) \
        .order_by('name', 'pk', 'installments__credits__role__order') \
        .only('name')

    # TODO: show cover of first installment with a credit on?

    context = {
        'creator': creator,
        'has_characters': Persona.objects.filter(creators__pk=creator.pk).exists(),
        'characters': characters,
        'has_series': Series.objects.filter(installments__credits__creator__pk=creator.pk).exists(),
        'series': series,
    }
    return render(request, 'metadata/creator.html', context)
