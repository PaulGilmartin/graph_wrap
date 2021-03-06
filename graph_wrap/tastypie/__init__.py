from graph_wrap.tastypie.graphql_view import graphql_view


def schema():
    from graph_wrap.tastypie.schema_factory import SchemaFactory
    return SchemaFactory.create_from_api()


__all__ = ['schema', 'graphql_view']
