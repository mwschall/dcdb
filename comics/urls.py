from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'comics'
urlpatterns = [
    path('', views.index, name='index'),
    path('installment/<int:installment>/next', views.installment_page, name='page'),
    path('installment/<int:installment>/page/<int:page_ord>', views.installment_page, name='page'),
    path('installment/<int:installment>', views.installment_detail, name='installment'),
    path('strip/<int:series>/page/<int:page_ord>', views.strip_page, name='strip_page'),
    path('series/<int:series>', RedirectView.as_view(url='/comics/', permanent=False), name='series'),
    path('strip/<int:series>', views.series_detail, name='strip'),
    path('thread/<int:thread>', views.thread_detail, name='thread'),
]
