from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

app_name = 'comics'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^installment/(?P<installment_id>[0-9]+)$', views.installment_detail, name='installment'),
    url(r'^installment/(?P<installment_id>[0-9]+)/page/(?P<page_idx>[0-9]+)$', views.installment_page, name='page'),
    url(r'^installment/(?P<installment_id>[0-9]+)/next$', views.installment_page, name='page'),
    url(r'^series/(?P<series_id>[0-9]+)$', RedirectView.as_view(url='/comics/', permanent=False), name='series'),
    url(r'^strip/(?P<series_id>[0-9]+)$', views.series_detail, name='strip'),
    url(r'^strip/(?P<series_id>[0-9]+)/page/(?P<page_idx>[0-9]+)$', views.strip_page, name='strip_page'),
    url(r'^thread/(?P<thread_id>[0-9]+)/$', views.thread_detail, name='thread'),
]
