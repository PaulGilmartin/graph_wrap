from __future__ import unicode_literals

import copy
import json
from abc import abstractmethod

from graph_wrap.graphql_transformer import transform_graphql_resolve_info


class GrapheneFieldResolver:
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


class QueryResolverBase(GrapheneFieldResolver):
    """Callable which acts as resolver for a field on the root Query."""
    def __init__(self, field_name, api):
        super(QueryResolverBase, self).__init__(field_name)
        self._api = copy.deepcopy(api)

    def rest_api_resolver_method(self, **kwargs):
        pass

    def __call__(self, root, info, **kwargs):
        get_request = transform_graphql_resolve_info(
            self._field_name, info, **kwargs)
        response = self._get_response(get_request, **kwargs)
        if str(response.status_code).startswith('4'):
            raise Exception(response.content)
        response_json = json.loads(response.content or '{}')
        return response_json

    @abstractmethod
    def _get_response(self, request, **kwargs):
        pass

    @abstractmethod
    def _build_selected_fields_api(self):
        pass
