from django.conf.urls import url

from . import views

app_name = 'comics'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<issue_id>[0-9]+)/$', views.issue_detail, name='issue'),
]
