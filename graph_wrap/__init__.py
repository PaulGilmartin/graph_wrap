from django.conf import settings

from graph_wrap.tastypie.graphql_resource import GraphQLResource
from graph_wrap.tastypie.schema_factory import SchemaFactory

__all__ = ['schema', 'GraphQLResource']


# Lazy evaluation so apps can load before use
def schema():
    return SchemaFactory.create_from_api(settings.TASTYPIE_API_PATH)
