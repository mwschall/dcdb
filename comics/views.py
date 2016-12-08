from itertools import groupby

import inflect
from django.shortcuts import render, get_object_or_404
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


def gen_page_links(page):
    installment_id = page.installment.id
    page_idx = page.order
    last_page = page.installment.num_pages - 1

    def page_link(page_num):
        return reverse('comics:page', args=[installment_id, page_num])

    data = {
        'first_url': page_link(0),
        'last_url': page_link(last_page),
        'thread_url': reverse('comics:installment', args=[installment_id]),
    }

    if page_idx > 0:
        data.update({'prev_url': page_link(page_idx-1)})
    if page_idx < last_page:
        data.update({'next_url': page_link(page_idx+1)})

    return data


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
def installment_detail(request, installment_id):
    installment = get_object_or_404(Installment, pk=installment_id)

    if request.accepted_renderer.format == 'json':
        serializer = InstallmentSerializer(instance=installment)
        data = serializer.data
        return Response(data)
    else:
        context = {
            'installment': installment,
            'credits': gen_credit_list(installment),
            'pages': installment.pages.all,
        }
        return Response(context, template_name='comics/installment.html')


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def installment_page(request, installment_id, page_idx):
    page = get_object_or_404(Page, installment_id=installment_id, order=page_idx)

    serializer = PageSerializer(instance=page)

    context = {
        'total_pages': page.installment.num_pages,
        'page': serializer.data,
        'index': page_idx,
        'links': gen_page_links(page),
    }

    return Response(context, template_name='comics/page.html')


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def series_detail(request, series_id):
    series = get_object_or_404(Series, pk=series_id)

    serializer = SeriesSerializer(instance=series)
    data = serializer.data
    return Response(data)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def strip_page(request, series_id, page_idx):
    series = get_object_or_404(Series, pk=series_id, is_strip=True)

    idx = int(page_idx)
    ins = series.pages[idx]

    serializer = StripInstallmentSerializer(instance=ins)

    context = {
        'total_pages': series.installments.count(),
        'page': serializer.data,
        'index': idx,
        'links': {
            'thread_url': reverse('comics:strip', args=[series_id]),
        },
    }

    return Response(context, template_name='comics/page.html')


@api_view(['GET'])
def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    context = {
        'thread': thread,
        'pages': thread.pages,
    }
    return render(request, 'comics/thread.html', context)
