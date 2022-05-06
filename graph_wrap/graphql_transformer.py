from __future__ import unicode_literals

from collections import defaultdict

from django.core.handlers.wsgi import WSGIRequest


def transform_graphql_resolve_info(
        root_field_name, resolve_info, **field_kwargs):
    transformer = GraphQLResolveInfoTransformer(
       root_field_name, resolve_info, **field_kwargs)
    root_field = next(
        field for field in resolve_info.field_asts if
        field.name.value == root_field_name
    )
    selected_fields = transformer.get_selected_fields(root_field)
    query_string = transformer.get_query_params(root_field)
    get_request = transformer.transform_graphql_request(
        selected_fields=selected_fields, query_string=query_string)
    return get_request


class GraphQLResolveInfoTransformer(object):
    def __init__(self, root_field_name, resolve_info, **field_kwargs):
        self._root_field_name = root_field_name
        self._resolve_info = resolve_info
        self._request = self._resolve_info.context
        self._field_kwargs = field_kwargs

    def transform_graphql_request(self, selected_fields, query_string):
        """Transforms input request to a GET request.

         Transforms the input request (which may be, for example,
         a POST request originally pointed at graphql endpoint),
         to the appropriate  GET request for a REST endpoint.
         """
        # TODO: Get correct path info for request
        # self._resolve_info.field_asts has info on the other filters
        environ = self._request.environ
        environ_overrides = dict(
            REQUEST_METHOD='GET',
            selected_fields=selected_fields,
        )
        if 'orm_filters' in self._field_kwargs:
            #query_string = self._field_kwargs['orm_filters']
            environ_overrides['QUERY_STRING'] = query_string
        environ.update(environ_overrides)
        get_request = WSGIRequest(environ)
        get_request.user = self._request.user
        get_request.content_type = self._request.content_type
        try:
            from rest_framework.settings import api_settings
        except ImportError:
            pass
        else:
            if api_settings.SEARCH_PARAM in self._field_kwargs:
                query = self._request.GET.copy()
                query.update(self._field_kwargs)
                get_request.GET = query
        return get_request

    def get_query_params(self, root_field):
        query_params = defaultdict(str)
        if root_field.arguments:
            query_string = ['&'.join(
                [f.value.value for f in root_field.arguments])]
            base_join = ''
            query_params = self._get_query_string(
                root_field, query_string=query_string, base_join=base_join)
        query_params = '&'.join([q for q in query_params])
        return query_params

    def _get_query_string(self, field, query_string, base_join):
        if hasattr(field.selection_set, 'selections'):
            selections_for_field = field.selection_set.selections
        else:
            fragment = self._get_fragment(field)
            selections_for_field = fragment.selection_set.selections

        for selected_field in selections_for_field:
            if hasattr(selected_field, 'selection_set'):
                if selected_field.selection_set and selected_field.arguments:
                    if base_join:
                        base_join += '__{}'.format(selected_field.name.value)
                    else:
                        base_join = selected_field.name.value
                    query_string.append('{}__{}'.format(base_join, '&'.join([
                        f.value.value for f in selected_field.arguments])))
                if selected_field.selection_set:
                    self._get_query_string(
                        selected_field,
                        query_string,
                        base_join,
                    )
            else:
                fragment = self._get_fragment(selected_field)
                self._get_query_string(
                    fragment,
                    query_string,
                    base_join,
                )
        return query_string




    def get_selected_fields(self, root_field):
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
        selected_fields = self._get_selected_fields(
            root_field, selected_fields={})
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
