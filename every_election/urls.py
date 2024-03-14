from core.views import HomeView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

handler500 = "dc_utils.urls.dc_server_error"

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^accounts/", include("django.contrib.auth.urls")),
    re_path(r"^$", HomeView.as_view(), name="home"),
    re_path(r"^organisations/", include("organisations.urls")),
    re_path(r"", include("elections.urls")),
    re_path(r"^api/", include(("api.urls", "api"), namespace="api")),
    re_path(r"^election_radar/", include("election_snooper.urls")),
    re_path(
        r"^robots\.txt$",
        TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),
]

if "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
        show_indexes=True,
    )

    from dc_utils.urls import dc_utils_testing_patterns

    urlpatterns += dc_utils_testing_patterns
