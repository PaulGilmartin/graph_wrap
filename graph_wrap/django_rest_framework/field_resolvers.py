from __future__ import unicode_literals

from abc import abstractmethod
import copy

import json
from functools import partial

from graph_wrap.graphql_transformer import transform_graphql_resolve_info


class GrapheneFieldResolver(object):
    """Callable which acts as resolver for a graphene field.

    Note: Callable object, and not simply a function, for two
    reasons:
    - To bind field_name to the class namespace on instantiation,
      which is important when dynamically building ObjectType
      resolver methods.
    - More easily extendable.
    """
    def __init__(self, field_name):
        self._field_name = field_name

    @abstractmethod
    def __call__(self, parent, info, **kwargs):
        """Resolves the appropriate field.

        The signature here matches that of a resolver method
        on a graphene ObjectType class.
        """
        pass


class JSONResolver(GrapheneFieldResolver):
    def __call__(self, parent, info, **kwargs):
        """Resolves the appropriate field from the parent JSON."""
        if parent:
            return parent[self._field_name]


class QueryResolver(GrapheneFieldResolver):
    """Callable which acts as resolver for a field on the root Query."""
    def __init__(self, field_name, api):
        super(QueryResolver, self).__init__(field_name)
        self._api = copy.deepcopy(api)

    def rest_api_resolver_method(self, **kwargs):
        pass

    def __call__(self, root, info, **kwargs):
        get_request = transform_graphql_resolve_info(
            self._field_name, info, **kwargs)
        self._api.serializer_class = self._build_selected_fields_cls(self._api)
        # Would be better if we could get following to work, but it
        # would involve mutating the class of the api instance, which
        # isn't thread safe?
        # Looking at our REST tests tell us what we should call as_view with
        # Maybe we can subclass the api class?
        # view_func = self._api.__class__.as_view({'get': 'list'})
        # response = view_func(get_request).render()
        resolver = self.rest_api_resolver_method(**kwargs)
        response = resolver(get_request).render()
        # handle bad status codes
        response_json = json.loads(response.content or '{}')
        return response_json

    def _build_selected_fields_cls(self, api):
        class SelectedFieldsSerializer(api.serializer_class):

            # is this __name__ working?
            # Main issue with this is that it may fail type checking
            # in user code.
            # Possible alternative is to bind this __init__
            # as we did the tastypie dehydrate?
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

        return SelectedFieldsSerializer


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
        return getattr(self._api, 'dispatch')


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
        return partial(
            getattr(self._api, 'dispatch'),
            pk=kwargs['id'],
            get='detail',
        )
