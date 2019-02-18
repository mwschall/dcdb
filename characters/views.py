from django.db.models.query import Prefetch
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view

from characters.models import Being
from comics.models import Installment, Page


@api_view(['GET'])
def being_index(request):
    beings = Being.objects.all()
    # TODO: group by name/classification/other
    context = {
        'beings': beings,
    }
    return render(request, 'characters/beings.html', context)


@api_view(['GET'])
def being_page(request, being):
    being = get_object_or_404(Being.objects, pk=being)
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
                                        INNER JOIN  characters_appearance ca1 
                                        ON          ca1.installment_id = ci0.id
                                        INNER JOIN  characters_persona cp0 
                                        ON          cp0.id = ca1.persona_id
                                WHERE   cp0.being_id = %s))
        ORDER  	BY "comics_series"."name"
        ''', [being.pk])

    context = {
        'being': being,
        'persona': being.primary_persona,
        'aka': ', '.join(being.aka.values_list('name', flat=True)),
        'first_issues': first_issues,
    }
    return render(request, 'characters/being.html', context)
