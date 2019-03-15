from itertools import groupby
from operator import attrgetter

import inflect
from django.db.models import Count, Case, When, OuterRef, Exists
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _, ungettext
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response

from comics.serializers import PageSerializer, InstallmentSerializer, SeriesSerializer, StripInstallmentSerializer
from metadata.models import Persona, Character
from .models import Installment, Page, Thread, Series

p = inflect.engine()


# See also: http://stackoverflow.com/questions/480214/
def fmt_credit_list(credit_list):
    if len({c.creator for c in credit_list}) == 1:
        return [(_("by"), (credit_list[0].creator,))]
    else:
        raw = [
            (str(r), tuple(map(lambda c: c.creator, cl)))
            for r, cl in groupby(credit_list, lambda c: c.role)
        ]
        return [(ungettext(r, p.plural(r), len(el)), el) for r, el in raw]


def gen_base():
    return reverse('comics:index')


def gen_page_links(page):
    installment_id = page.installment.id
    page_ord = page.order
    last_page = page.installment.num_pages - 1

    def page_link(page_num):
        return reverse('comics:page', args=[installment_id, page_num])

    data = {
        'first_url': page_link(0),
        'last_url': page_link(last_page),
        'thread_url': reverse('comics:installment', args=[installment_id]),
    }

    if page_ord > 0:
        data.update({'prev_url': page_link(page_ord-1)})
    if page_ord < last_page:
        data.update({'next_url': page_link(page_ord+1)})

    return data


def gen_thread_links(instance):
    if isinstance(instance, Installment):
        next_id = instance.next_id
        return {
            'thread': reverse('comics:installment', args=[instance.id]),
            'next': reverse('comics:page', args=[next_id, 0]) if next_id else '',
            'parent': reverse('comics:series', args=[instance.series_id]),
        }
    elif isinstance(instance, Series):
        if instance.is_strip:
            return {
                'thread': reverse('comics:strip', args=[instance.id]),
            }


@api_view(['GET'])
def index(request):
    threads = Thread.objects.all()
    strips = Series.objects.filter(is_strip=True)
    installments = Installment.objects.filter(series__is_strip=False)
    context = {
        'threads': threads,
        'strips': strips,
        'installments': installments,
    }
    return render(request, 'comics/index.html', context)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def installment_detail(request, installment):
    installment = get_object_or_404(Installment, pk=installment)

    if request.accepted_renderer.format == 'json':
        serializer = InstallmentSerializer(instance=installment)
        context = {
            'thread': serializer.data,
            'links': gen_thread_links(installment),
        }
        return Response(context)

    credit_list = installment.credits \
        .select_related('role', 'creator') \
        .all()

    # Notes:
    # - list each Character once
    # - use primary_persona if featured, else go by page count
    # - final sorting by total appearances, but by name might be better
    personas = Persona.objects \
        .order_by() \
        .filter(appearances__installment=installment,
                appearances__is_spoiler=False) \
        .annotate(app_count=Count(Case(When(appearances__installment=installment, then='pk'))),
                  is_primary=Exists(Character.objects.filter(primary_persona=OuterRef('pk')))) \
        .order_by('character', '-is_primary', '-app_count', 'name')

    def get_char(g):
        # star = next(g)
        # star.also_as = [q.name for q in g]
        pl = list(g)
        star = pl[0]
        star.also_as = pl[1:]
        star.app_total = sum([pa.app_count for pa in pl])
        return star

    appearances = sorted([get_char(g) for _, g in groupby(personas, lambda m: m.character)],
                         key=attrgetter('app_total'), reverse=True)

    context = {
        'installment': installment,
        'credits': fmt_credit_list(credit_list),
        'pages': installment.pages.all(),
        'appearances': appearances,
    }
    return Response(context, template_name='comics/installment.html')


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def installment_page(request, installment, page_ord='next'):
    if page_ord is 'next':
        installment = get_object_or_404(Installment, pk=installment)
        page = installment.pages.last()
        print(page.order)
    else:
        page = get_object_or_404(Page, installment=installment, order=page_ord)
        installment = page.installment

    serializer = PageSerializer(instance=page)

    initial_state = {
        'base': gen_base(),
        'page': serializer.data,
        'index': page.order,
        'links': gen_thread_links(installment),
        'thread': {
            'name': installment.name,
            'num_pages': installment.num_pages,
        },
    }

    return Response({'initial_state': initial_state}, template_name='comics/page.html')


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def series_detail(request, series):
    series = get_object_or_404(Series, pk=series)

    if request.accepted_renderer.format == 'json':
        serializer = SeriesSerializer(instance=series)
        context = {
            'links': gen_thread_links(series),
            'thread': serializer.data,
        }
        return Response(context)

    installments = series.installments.order_by('-ordinal')

    context = {
        'series': series,
        'installments': installments,
    }
    return render(request, 'comics/series.html', context)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def strip_page(request, series, page_ord):
    series = get_object_or_404(Series, pk=series, is_strip=True)

    idx = int(page_ord)
    ins = series.pages[idx]

    serializer = StripInstallmentSerializer(instance=ins)

    initial_state = {
        'base': gen_base(),
        'page': serializer.data,
        'index': idx,
        'links': {
            'thread': reverse('comics:strip', args=[series]),
        },
        'thread': {
            'name': series.name,
            'num_pages': series.installments.count(),
        }
    }

    return Response({'initial_state': initial_state}, template_name='comics/page.html')


@api_view(['GET'])
def thread_detail(request, thread):
    thread = get_object_or_404(Thread, pk=thread)
    context = {
        'thread': thread,
        'pages': thread.pages,
    }
    return render(request, 'comics/thread.html', context)
