from django.shortcuts import render, get_object_or_404

from .models import Installment


def index(request):
    issues = Installment.objects.all()
    context = {'issues': issues}
    return render(request, 'comics/index.html', context)


def issue_detail(request, issue_id):
    issue = get_object_or_404(Installment, pk=issue_id)
    return render(request, 'comics/issue.html', {'issue': issue})
