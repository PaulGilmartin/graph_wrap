from __future__ import unicode_literals

from django.core.handlers.wsgi import WSGIRequest


def transform_graphql_resolve_info(
        root_field_name, resolve_info, **field_kwargs):
    transformer = GraphQLResolveInfoTransformer(
       root_field_name, resolve_info, **field_kwargs)
    selected_fields = transformer.transform_resolve_info()
    get_request = transformer.transform_graphql_request(
        selected_fields=selected_fields)
    return get_request


class GraphQLResolveInfoTransformer(object):
    def __init__(self, root_field_name, resolve_info, **field_kwargs):
        self._root_field_name = root_field_name
        self._resolve_info = resolve_info
        self._request = self._resolve_info.context
        self._query_string = '{}'.format(
            field_kwargs.get('orm_filters', ''))

    def transform_graphql_request(self, **environ_params):
        """Transforms input request to a GET request.

         Transforms the input request (which may be, for example,
         a POST request originally pointed at graphql endpoint),
         to the appropriate  GET request for a REST endpoint.
         """
        # TODO: Get correct path info for request - see Api.top_level
        environ = self._request.environ
        environ_overrides = dict(
            REQUEST_METHOD='GET',
            QUERY_STRING=self._query_string,
            **environ_params
        )
        environ.update(environ_overrides)
        get_request = WSGIRequest(environ)
        get_request.user = self._request.user
        return get_request

    def transform_resolve_info(self):
        """Transform ResolveInfo object into a graph-like dictionary.

         Transform a graphql ResolveInfo object into a graph-like
         dictionary which can be passed around in a WSGI
         request to allow dynamic selection of fields in
         REST-based resources.

         Example:

         The following query

            query {
                    all_books {
                        id
                        title
                        author {
                                    id
                                    first_name
                                    books {
                                        title
                                    }
                            }
                    }
            }

        is transformed to

            {u'id': {},
             u'title': {},
             u'author':
             {u'books':
                {u'title': {}},
            u'first_name': {},
            u'id': {}},
            }
        """
        field = next(
            field for field in self._resolve_info.field_asts if
            field.name.value == self._root_field_name
        )
        selected_fields = self._get_selected_fields(
            field, {})
        return selected_fields

    def _get_selected_fields(self, field, selected_fields):
        if hasattr(field.selection_set, 'selections'):
            selections_for_field = field.selection_set.selections
        else:
            fragment = self._get_fragment(field)
            selections_for_field = fragment.selection_set.selections

        for selected_field in selections_for_field:
            if hasattr(selected_field, 'selection_set'):
                selected_fields[selected_field.name.value] = {}
                if selected_field.selection_set:
                    self._get_selected_fields(
                        selected_field,
                        selected_fields[selected_field.name.value],
                    )
            else:
                fragment = self._get_fragment(selected_field)
                self._get_selected_fields(
                    fragment,
                    selected_fields,
                )
        return selected_fields

    def _get_fragment(self, field):
        try:
            return self._resolve_info.fragments[field.name.value]
        except KeyError:
            raise TransformationError('Unable to transform!')


class TransformationError(Exception):
    pass
