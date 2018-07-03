from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

from core.views import HomeView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'^organisations/', include('organisations.urls')),
    url(r'', include('elections.urls')),
    url(r'^api/', include('api.urls', namespace='api')),
    url('^markdown/', include('django_markdown.urls')),
    url(r'^election_radar/', include('election_snooper.urls')),
    url(r'^email/', include('dc_signup_form.urls')),
    url(r'^robots\.txt$', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
]

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT, show_indexes=True)
