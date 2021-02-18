from django.db.models import Func


class JsonbSet(Func):
    """
    Implements Postgres jsonb_set function
    https://www.postgresql.org/docs/current/functions-json.html

    First arg is name of jsonbfield enclosed in ". eg: "tags"
    Second arg is path through json obj, wrapped in Value. eg: Value('{"BAZ",0,"bar"}')
        given obj: {"BAZ":[{"bar":"foo"}]
    Third arg is value to set path defined in 2nd arg to. eg: Value('{"a": "b"}') or Value("a")
    Forth arg is 'create_if_missing' bool.
    See tests and add_tags management command for examples of usage
    """

    function = "jsonb_set"
    arity = 4
