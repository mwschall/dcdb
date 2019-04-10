from django.urls import path

from . import views

app_name = 'comics'
urlpatterns = [
    path('', views.index, name='index'),
    path('installment/<suuid:installment>/next', views.installment_page, name='page'),
    path('installment/<suuid:installment>/page/<int:page_ord>', views.installment_page, name='page'),
    path('installment/<suuid:installment>', views.installment_detail, name='installment'),
    path('strip/<suuid:series>/page/<int:page_ord>', views.strip_page, name='strip_page'),
    path('series/<suuid:series>', views.series_detail, name='series'),
    path('strip/<suuid:series>', views.series_detail, name='strip'),
    path('thread/<suuid:thread>', views.thread_detail, name='thread'),
]
