from django.urls import path

from . import views

app_name = 'metadata'
urlpatterns = [
    path('characters/', views.character_index, name='index'),
    path('characters/<suuid:character>/<slug:slug_name>', views.character_page, name='character'),
    path('characters/<suuid:character>', views.character_page, name='character'),
    path('creators/', views.creator_index, name='creators'),
    path('creators/<suuid:creator>/<slug:slug_name>', views.creator_page, name='creator'),
    path('creators/<suuid:creator>', views.creator_page, name='creator'),
]
