from django.views.decorators.http import require_http_methods
from graphene_django.views import GraphQLView


@require_http_methods(['POST'])
def graphql_view(request):
    from graph_wrap.tastypie import schema
    schema = schema()
    view = GraphQLView.as_view(schema=schema)
    return view(request)

