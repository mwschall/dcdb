from itertools import groupby

import inflect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext as _, ungettext
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response

from comics.serializers import PageSerializer, InstallmentSerializer, SeriesSerializer, StripInstallmentSerializer
from .models import Installment, Page, get_full_credits, Thread, Series

p = inflect.engine()


# See also: http://stackoverflow.com/questions/480214/
def gen_credit_list(item):
    credit_list = get_full_credits(item)
    if len({c.entity for c in credit_list}) == 1:
        return [(_("by"), credit_list[0].entity)]
    else:
        # TODO: sort by role importance
        raw = [
            (str(r), sorted(map(lambda c: str(c.entity), rcl)))
            for r, rcl
            in groupby(credit_list, lambda c: c.role)
        ]
        return [(ungettext(r, p.plural(r), len(el)), ", ".join(el)) for r, el in raw]


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
    else:
        context = {
            'installment': installment,
            'credits': gen_credit_list(installment),
            'pages': installment.pages.all,
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
    else:
        return redirect('comics:index')


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
