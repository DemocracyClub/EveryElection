from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

from core.views import HomeView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^organisations/', include('organisations.urls')),
    url(r'', include('elections.urls')),
    url(r'^api/', include('api.urls')),
    url('^markdown/', include('django_markdown.urls')),
    url(r'^election_radar/', include('election_snooper.urls')),
]

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT, show_indexes=True)
