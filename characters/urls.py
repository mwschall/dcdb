from django.conf.urls import url

from . import views

app_name = 'characters'
urlpatterns = [
    url(r'^$', views.being_index, name='index'),
    # url(r'^being/$', views.being_index, name='beings'),
    url(r'^being/(?P<being>[0-9]+)$', views.being_page, name='being'),
]
