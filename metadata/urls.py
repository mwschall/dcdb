from django.urls import path

from . import views

app_name = 'metadata'
urlpatterns = [
    path('characters/', views.character_index, name='index'),
    path('characters/<suuid:character>', views.character_page, name='character'),
    path('creators/', views.creator_index, name='creators'),
    path('creators/<suuid:creator>', views.creator_page, name='creator'),
]
