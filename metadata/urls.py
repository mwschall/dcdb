from django.urls import path

from . import views

app_name = 'metadata'
urlpatterns = [
    path('beings/', views.being_index, name='index'),
    path(r'beings/<int:being>', views.being_page, name='being'),
]
