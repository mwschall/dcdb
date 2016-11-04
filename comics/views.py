import itertools

import inflect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _, ungettext

from .models import Installment, Page, get_full_credits

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
            in itertools.groupby(credit_list, lambda c: c.role)
        ]
        return [(ungettext(r, p.plural(r), len(el)), ", ".join(el)) for r, el in raw]


def index(request):
    installments = Installment.objects.all()
    context = {'installments': installments}
    return render(request, 'comics/index.html', context)


def installment_detail(request, installment_id):
    installment = get_object_or_404(Installment, pk=installment_id)
    context = {
        'installment': installment,
        'credits': gen_credit_list(installment),
        'pages': installment.page_set.all,
    }
    return render(request, 'comics/installment.html', context)


def ins_page_detail(request, installment_id, page_idx):
    page_idx = int(page_idx)
    page = get_object_or_404(Page, installment_id=installment_id, order=page_idx)
    prev_idx = page_idx - 1 if page_idx > 0 else None
    next_idx = page_idx + 1 if page_idx < page.installment.num_pages - 1 else None
    context = {
        'page': page,
        'prev_idx': prev_idx,
        'next_idx': next_idx,
    }
    return render(request, 'comics/page.html', context)
