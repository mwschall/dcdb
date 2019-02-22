from django.urls import path

from . import views

app_name = 'metadata'
urlpatterns = [
    path('characters/', views.character_index, name='index'),
    path(r'characters/<int:character>', views.character_page, name='character'),
]
