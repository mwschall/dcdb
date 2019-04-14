from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import register_converter, path
from django.views.generic import RedirectView

from comics.converters import ShortUUIDConverter, NumeralConverter

register_converter(NumeralConverter, 'num')
register_converter(ShortUUIDConverter, 'suuid')

urlpatterns = [
    path('', RedirectView.as_view(url='/comics/', permanent=False)),
    path('', include('comics.urls', namespace='comics')),
    path('', include('metadata.urls', namespace='metadata')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
