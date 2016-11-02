from django.shortcuts import render, get_object_or_404

from .models import Installment, Page


def index(request):
    issues = Installment.objects.all()
    context = {'issues': issues}
    return render(request, 'comics/index.html', context)


def issue_detail(request, issue_id):
    issue = get_object_or_404(Installment, pk=issue_id)
    return render(request, 'comics/issue.html', {'issue': issue})


def page_detail(request, issue_id, page_idx):
    page_idx = int(page_idx)
    page = get_object_or_404(Page, installment_id=issue_id, order=page_idx)
    prev_idx = page_idx-1 if page_idx > 0 else None
    next_idx = page_idx+1 if page_idx < page.installment.num_pages-1 else None
    return render(request, 'comics/page.html', {
        'page': page,
        'prev_idx': prev_idx,
        'next_idx': next_idx,
    })
