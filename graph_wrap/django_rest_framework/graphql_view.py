from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView


# See https://github.com/PaulGilmartin/graph_wrap/issues/5 for csrf_exempt
# rationale.
@csrf_exempt
def graphql_view(request):
    from graph_wrap.django_rest_framework import schema
    schema = schema()
    view = GraphQLView.as_view(schema=schema)
    return view(request)

