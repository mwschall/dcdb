from django.urls import path, include

from . import views

app_name = 'comics'

installment_patterns = [
    path('p<int:page>', views.installment_page, name='page'),
    path('next', views.installment_page),
    path('', views.installment_detail, name='installment'),
]

series_patterns = [
    path('i<num:number>/', include(installment_patterns)),
    path('<int:ordinal>/', include(installment_patterns)),
    path('', views.series_detail, name='series'),
]

strip_patterns = [
    path('p<int:page>', views.strip_page, name='strip_page'),
    path('', views.series_detail, name='strip'),
]

urlpatterns = [
    path('comics/', views.index, name='index'),
    path('installment/<suuid:installment>/p<int:page>', views.page_redirect, name='page'),
    path('installment/<suuid:installment>', views.installment_redirect, name='installment'),
    path('series/<suuid:series>/', include(series_patterns)),
    path('series/<slug:series>/', include(series_patterns)),
    path('strip/<suuid:series>/', include(strip_patterns)),
    path('strip/<slug:series>/', include(strip_patterns)),
    path('thread/<suuid:thread>', views.thread_detail, name='thread'),
]
