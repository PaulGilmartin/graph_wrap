from __future__ import unicode_literals

import json
import graphene
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from graph_wrap.django_rest_framework.field_resolvers import JSONResolver
import six


class ApiTransformer(object):
    def __init__(self, api, type_mapping=None):
        self._api = api
        self._root_serializer = api.get_serializer()
        self._all_serializers = []
        self._collect_nested_serializers(self._root_serializer)
        self._root_serializer, *self._nested_serializers = self._all_serializers
        self._root_graphene_type_name = u'{}_type'.format(self._api.basename)
        self.type_mapping = type_mapping or dict()

    def root_type(self):
        root_type = SerializerTransformer(
            self._root_serializer,
            self.type_mapping,
            self._root_graphene_type_name,
        ).graphene_object_type()
        return root_type

    def non_root_types(self):
        non_root_types = []
        for nested in self._nested_serializers:
            nested_transformed = SerializerTransformer(
                nested, self.type_mapping).graphene_object_type()
            non_root_types.append(nested_transformed)
            # if isinstance(nested.parent, ListSerializer):
            #     # For 'to many' fields
            #     list_serializer = nested.parent
            #     self.type_mapping[
            #         (list_serializer.field_name,
            #          list_serializer.parent)] = nested_transformed
            # else:
            #     self.type_mapping[
            #         (nested.field_name, nested.parent)] = nested_transformed
        return non_root_types

    def _collect_nested_serializers(self, serializer):
        for _field_name, field in serializer.fields.items():
            nested_serializer = self._get_nested_serializer(field)
            if nested_serializer:
                self._collect_nested_serializers(
                    nested_serializer)
        self._all_serializers.insert(0, serializer)

    def _get_nested_serializer(self, field):
        if hasattr(field, 'fields'):
            return field
        elif hasattr(field, 'child'):
            return field.child
        return None


class SerializerTransformer(object):
    def __init__(
            self,
            serializer,
            type_mapping,
            graphene_type_name='',
    ):
        self._serializer = serializer
        self._model_name = self._serializer.Meta.model.__name__.lower()
        self.type_mapping = type_mapping
        self._graphene_type_name = (
                graphene_type_name or self._build_graphene_type_name())
        self._graphene_object_type_class_attrs = dict()

    def graphene_object_type(self):
        try:
            return self.type_mapping[self._graphene_type_name]
        except KeyError:
            for field in self._serializer.fields.values():
                self._add_field_data(field)
            graphene_type = type(
                self._graphene_type_name,
                (ObjectType,),
                self._graphene_object_type_class_attrs,
            )
            self.type_mapping[self._graphene_type_name] = graphene_type
            return graphene_type

    def _build_graphene_type_name(self):
        if isinstance(self._serializer.parent, ListSerializer):
            named_field = self._serializer.parent
        else:
            named_field = self._serializer
        serializer_cls_name = self._serializer.__class__.__name__
        if serializer_cls_name == 'NestedSerializer':
            model = named_field.parent.Meta.model.__name__.lower()
            return '{}__{}_type'.format(model, named_field.field_name)
        else:
            return '{}_type'.format(named_field.field_name)

    def _add_field_data(self, field):
        field_transformer = FieldTransformer.get_transformer(
            field, self.type_mapping)
        graphene_field = field_transformer.graphene_field()
        self._graphene_object_type_class_attrs[field.field_name] = graphene_field
        resolver_method_name = 'resolve_{}'.format(field.field_name)
        self._graphene_object_type_class_attrs[resolver_method_name] = (
            field_transformer.graphene_field_resolver_method())


class FieldTransformer:
    _graphene_type = None

    def __init__(self, field, type_mapping):
        # these arguments couple it a bit too much, can we improve?
        self._field = field
        self.type_mapping = type_mapping

    @classmethod
    def get_transformer(cls, field, type_mapping):
        if isinstance(field, serializers.ModelSerializer):
            transformer_class = RelatedValuedFieldTransformer
        elif hasattr(field, 'child') and isinstance(
                field.child, serializers.ModelSerializer):
            # for ListSerializers from M2M fields
            transformer_class = RelatedValuedFieldTransformer
        else:
            serializer_field_to_transformer = {
                'BooleanField': BooleanValuedFieldTransformer,
                'NullBooleanField': BooleanValuedFieldTransformer,
                'IntegerField': IntegerValuedFieldTransformer,
                'FloatField': FloatValuedFieldTransformer,
                'DecimalField': DecimalValuedFieldTransformer,
                'ListField': ListValuedFieldTransformer,
                'DictField': DictValuedFieldTransformer,
                'HStoreField': DictValuedFieldTransformer,
                'JSONField': DictValuedFieldTransformer,
                'CharField': StringValuedFieldTransformer,
                'DateTimeField': StringValuedFieldTransformer,
                'EmailField': StringValuedFieldTransformer,
                'RelatedField': StringValuedFieldTransformer,
                'HyperlinkedRelatedField': StringValuedFieldTransformer,
                'PrimaryKeyRelatedField': StringValuedFieldTransformer,
                'ManyRelatedField': ListOfStringsValuedFieldTransformer,
            }
            # Can we make this easily extendable for clients?
            try:
                transformer_class = serializer_field_to_transformer[
                    field.__class__.__name__]
            except KeyError:
                raise KeyError(
                    '{} not a recognised field type'.format(field.__class__))
        return transformer_class(field, type_mapping)

    def graphene_field(self):
        pass

    def graphene_field_resolver_method(self):
        return JSONResolver(self._graphene_field_name())

    def _graphene_field_name(self):
        return self._field.field_name

    def _graphene_field_required(self):
        return not self._field.allow_null


class ScalarValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'scalar' valued tastypie field.

    Base transformer for converting any tastypie field which is not a
    subclass of RelatedField.
    """

    def graphene_field(self):
        return self._graphene_type(
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )


class RelatedValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'related' field."""
    def __init__(self, field, type_mapping):
        super(RelatedValuedFieldTransformer, self).__init__(
            field, type_mapping)
        self._field_class = field.__class__
        self._is_to_many = getattr(field, 'many', False)

    def graphene_field(self):
        wrapper = graphene.List if self._is_to_many else graphene.Field
        graphene_field = wrapper(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )
        return graphene_field

    @property
    def _graphene_type(self):
        # Needs to be lazy since at this point the related
        # type may not yet have been created
        return lambda: self.type_mapping[self._build_graphene_type_name()]

    def _build_graphene_type_name(self):
        if isinstance(self._field.parent, ListSerializer):
            named_field = self._field.parent
        else:
            named_field = self._field
        serializer_cls_name = self._field.__class__.__name__
        if serializer_cls_name == 'NestedSerializer':
            model = named_field.parent.Meta.model.__name__.lower()
            return '{}__{}_type'.format(model, named_field.field_name)
        else:
            return '{}_type'.format(named_field.field_name)


class StringValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class IntegerValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Int


class FloatValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Float


class BooleanValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Boolean


class DecimalValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Decimal


class Dict(graphene.Scalar):
    """Custom scalar to transform 'dict' type tastypie fields."""
    @staticmethod
    def serialize(dt):
        if isinstance(dt, six.string_types):
            return json.loads(dt)
        return dt


class DictValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Dict


class ListValuedFieldTransformer(FieldTransformer):
    _graphene_type = GenericScalar

    def graphene_field(self):
        return graphene.List(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )


class ListOfStringsValuedFieldTransformer(
        ListValuedFieldTransformer):
    _graphene_type = graphene.String

