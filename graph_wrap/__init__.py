from graph_wrap.tastypie.graphql_resource import GraphQLResource

__all__ = ['schema', 'GraphQLResource']


# Lazy evaluation so apps can load before use
def schema():
    from graph_wrap.tastypie.schema_factory import SchemaFactory
    return SchemaFactory.create_from_api()


def django_rest_schema():
    from graph_wrap.django_rest_framework.schema_factory import SchemaFactory
    return SchemaFactory.create_from_api()
