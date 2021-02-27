from __future__ import unicode_literals

import copy

import json
from functools import partial

from graph_wrap.graphql_transformer import transform_graphql_resolve_info
from graph_wrap.shared.field_resolvers import GrapheneFieldResolver


class QueryResolver(GrapheneFieldResolver):
    def __init__(self, field_name, api):
        super(QueryResolver, self).__init__(field_name)
        self._api = copy.deepcopy(api)

    def rest_api_resolver_method(self, **kwargs):
        pass

    def __call__(self, root, info, **kwargs):
        get_request = transform_graphql_resolve_info(
            self._field_name, info, **kwargs)
        resolver = self.rest_api_resolver_method(**kwargs)
        response = resolver(get_request).render()
        # handle bad status codes
        response_json = json.loads(response.content or '{}')
        return response_json

    def _build_selected_fields_api(self):

        class SelectedFieldsSerializer(self._api.serializer_class):

            __name__ = self._api.__class__.serializer_class.__name__

            def __init__(self, *args, **kwargs):
                request = self._kwargs['context']['request']
                selected_fields = request.environ.get('selected_fields', [])
                super().__init__(*args, **kwargs)
                self._set_selected_fields(self, selected_fields)

            def _set_selected_fields(self, serializer, selected_fields):
                allowed = set(selected_fields)
                existing = set(serializer.fields)
                for field_name in existing - allowed:
                    serializer.fields.pop(field_name)
                for field_name, field in serializer.fields.items():
                    if hasattr(field, 'child'):
                        field = field.child
                    if not hasattr(field, 'fields'):
                        continue
                    self._set_selected_fields(field, selected_fields[field_name])

        class SelectedFieldsView(self._api.__class__):
            serializer_class = SelectedFieldsSerializer

        return SelectedFieldsView


class AllItemsQueryResolver(QueryResolver):
    """Callable which acts as resolver for an 'all_items' field' on the Query.

    For example, if we had a ProfileAPI with underlying
    Django model 'Profile', an instance of this class provides
    functionality for the 'resolve_all_profiles' resolver
    on the root Query (analogous to a GET request to the /profile
    list endpoint in REST terms).
    """
    def __call__(self, root, info, **kwargs):
        response_json = super(AllItemsQueryResolver, self).__call__(
            root, info, **kwargs)
        return response_json

    def rest_api_resolver_method(self, **kwargs):
        selected_fields_cls = self._build_selected_fields_api()
        return selected_fields_cls.as_view(
            actions={'get': 'list'},
            suffix='List',
            basename=self._api.basename,
            detail=False,
        )


class SingleItemQueryResolver(QueryResolver):
    """Callable which acts as resolver for an 'single item' field' on the Query.

    For example, if we had an ProfileAPI with underlying
    Django model 'Profile', an instance of this class provides
    functionality for the 'resolve_profile' resolver
    on the root Query. Note in this case, we are required to
    supply an 'id' argument in the kwargs passed to __call__.
    (This  to a GET request to the /profile/{id} detail endpoint
     in REST terms)
    """

    def rest_api_resolver_method(self, **kwargs):
        selected_fields_cls = self._build_selected_fields_api()
        return partial(
            selected_fields_cls.as_view(
                actions={'get': 'retrieve'},
                suffix='Instance',
                basename=self._api.basename,
                detail=True,
            ),
            pk=kwargs['id'],
        )
