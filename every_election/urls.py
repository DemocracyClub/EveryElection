from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings

from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='home.html'), name="home"),
    url(r'^organisations/', include('organisations.urls')),
]

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT)
