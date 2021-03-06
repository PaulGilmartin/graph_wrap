from graphene_django.views import GraphQLView
from rest_framework.decorators import api_view


@api_view(['POST'])
def graphql_view(request):
    from graph_wrap.tastypie import schema
    schema = schema()
    view = GraphQLView.as_view(schema=schema)
    return view(request)

