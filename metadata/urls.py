from django.urls import path

from . import views

app_name = 'metadata'
urlpatterns = [
    path('characters/', views.character_index, name='index'),
    path('characters/<int:character>', views.character_page, name='character'),
    path('creators/', views.creator_index, name='creators'),
    path('creators/<int:creator>', views.creator_page, name='creator'),
]
