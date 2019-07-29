from django_global_request.middleware import get_request


class DbRouter:
    def db_for_read(self, model, **hints):
        request = get_request()

        try:
            if "/api" in request.path:
                return "replicas"
        except AttributeError:
            pass

        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
