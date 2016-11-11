from django.conf.urls import url

from . import views

app_name = 'comics'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^installment/(?P<installment_id>[0-9]+)/$', views.installment_detail, name='installment'),
    url(r'^installment/(?P<installment_id>[0-9]+)/page/(?P<page_idx>[0-9]+)$', views.installment_page, name='page'),
    url(r'^thread/(?P<thread_id>[0-9]+)/$', views.thread_detail, name='thread'),
]
