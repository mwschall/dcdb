from django.conf.urls import url

from . import views

app_name = 'metadata'
urlpatterns = [
    url(r'^beings/$', views.being_index, name='index'),
    # url(r'^being/$', views.being_index, name='beings'),
    url(r'^beings/(?P<being>[0-9]+)$', views.being_page, name='being'),
]
