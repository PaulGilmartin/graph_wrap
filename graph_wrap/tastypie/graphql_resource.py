from graphene_django.settings import GrapheneSettings
from graphene_django.views import GraphQLView
from tastypie.resources import Resource


class GraphQLResource(Resource):
    class Meta:
        resource_name = 'graphql'
        allowed_methods = ['post']

    def dispatch(self, request_type, request, **kwargs):
        schema = GrapheneSettings().SCHEMA()
        view = GraphQLView.as_view(schema=schema)
        return view(request)

