from django.conf import settings


def global_settings(request):
    return {"SERVER_ENVIRONMENT": getattr(settings, "SERVER_ENVIRONMENT", None)}
