from __future__ import unicode_literals

from graphene_django.views import GraphQLView
from tastypie.resources import Resource


class GraphQLResource(Resource):
    class Meta:
        resource_name = 'graphql'
        allowed_methods = ['post']

    def dispatch(self, request_type, request, **kwargs):
        from graph_wrap.tastypie import schema
        schema = schema()
        view = GraphQLView.as_view(schema=schema)
        return view(request)

