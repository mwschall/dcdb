from itertools import groupby
from operator import attrgetter

from django.db.models import Count, Case, When, OuterRef, Exists, F, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response

from comics.serializers import PageSerializer, InstallmentSerializer, SeriesSerializer, StripInstallmentSerializer
from metadata.models import Persona, Character, Credit, Creator
from .models import Installment, Page, Thread, Series


# See also: http://stackoverflow.com/questions/480214/
def gen_credit_list(credit_list):
    pk_set = set()

    def get_creator(entry):
        if hasattr(entry, 'creator'):
            c = entry.creator
        else:
            c = Creator(**{k.split('__')[1]: v
                           for k, v in entry.items()
                           if k.startswith('creator__')})
        pk_set.add(c.pk)
        try:
            c.credit_count = entry.get('credit_count')
        except AttributeError:
            pass
        return c

    def get_role(entry):
        if hasattr(entry, 'role'):
            return str(entry.role)
        return getattr(entry, 'role_name', entry.get('role_name'))

    raw = [(rn, [get_creator(c) for c in cl])
           for rn, cl in groupby(credit_list, get_role)]

    return [(_("by"), raw[0][1][:1])] if len(pk_set) == 1 else raw


def gen_base():
    return '/'


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


def get_series_or_404(series, *args, **kwargs):
    return get_object_or_404(Series.display_objects,
                             Q(pk=series) | Q(slug=series),
                             *args, **kwargs)


def get_inst_or_404(series, number=None, ordinal=None, **_):
    if 'number' is not None:
        return get_object_or_404(Installment, series=series, number=number)
    else:
        return get_object_or_404(Installment, series=series, ordinal=ordinal)


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


def installment_redirect(request, installment):
    installment = get_object_or_404(Installment, pk=installment)
    return redirect(installment.get_absolute_url())


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def installment_detail(request, series, **kwargs):
    series = get_series_or_404(series)
    installment = get_inst_or_404(series, **kwargs)

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
        'series': series,
        'installment': installment,
        'credits': gen_credit_list(credit_list),
        'pages': installment.pages.all(),
        'appearances': appearances,
    }
    return Response(context, template_name='comics/installment.html')


def page_redirect(request, installment, page):
    installment = get_object_or_404(Installment, pk=installment)
    page = get_object_or_404(Page, installment=installment, order=page)
    return redirect(page.get_absolute_url())


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def installment_page(request, series, **kwargs):
    series = get_series_or_404(series)
    installment = get_inst_or_404(series, **kwargs)

    if 'page' in kwargs:
        page = get_object_or_404(Page, installment=installment, order=kwargs['page'])
    else:
        page = installment.pages.last()

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
    series = get_series_or_404(series)

    if request.accepted_renderer.format == 'json':
        serializer = SeriesSerializer(instance=series)
        context = {
            'links': gen_thread_links(series),
            'thread': serializer.data,
        }
        return Response(context)

    credit_list = Credit.objects \
        .filter(installment__series=series) \
        .values('role', 'creator') \
        .annotate(role_name=F('role__name'),
                  credit_count=Count(F('creator__pk'))) \
        .order_by('role__order', '-credit_count', 'creator__working_name') \
        .values('role_name',
                'credit_count',
                'creator__pk',
                'creator__working_name',
                'creator__avatar')

    installments = series.installments \
        .order_by('-ordinal') \
        .iterator()

    context = {
        'series': series,
        'credits': gen_credit_list(credit_list),
        'num_installments': series.installment_count,
        'installments': installments,
    }
    return render(request, 'comics/series.html', context)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def strip_page(request, series, page):
    series = get_series_or_404(series, is_strip=True)

    idx = int(page)
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
