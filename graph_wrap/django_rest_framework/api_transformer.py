from __future__ import unicode_literals

import json
import graphene
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from graph_wrap.shared.query_resolver import JSONResolver
import six


class ApiTransformer:
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
            type_mapping=None,
            graphene_type_name='',
    ):
        self._serializer = serializer
        self.type_mapping = type_mapping if type_mapping is not None else dict()
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
            model = named_field.Meta.model.__name__.lower()
            type_name = '{}_type'.format(model)
            types_for_model = [
                t for t in self.type_mapping if t.startswith(type_name)]
            if types_for_model:
                type_name = '{}_{}'.format(type_name, len(types_for_model) + 1)
            return type_name

    def _add_field_data(self, field):
        field_transformer = FieldTransformer.get_transformer(
            field, self.type_mapping)
        graphene_field = field_transformer.graphene_field()
        self._graphene_object_type_class_attrs[field.field_name] = graphene_field
        resolver_method_name = 'resolve_{}'.format(field.field_name)
        self._graphene_object_type_class_attrs[resolver_method_name] = (
            field_transformer.graphene_field_resolver_method())


class FieldTransformer:
    graphene_type = None

    def __init__(self, field, type_mapping=None):
        self._field = field
        self.type_mapping = type_mapping if type_mapping is not None else dict()

    @classmethod
    def get_transformer(cls, field, type_mapping):
        if hasattr(field, 'child') and isinstance(
                field.child, serializers.ModelSerializer):
            # for ListSerializers from M2M fields
            return RelatedValuedFieldTransformer(field, type_mapping)

        base_types = {
            serializers.BooleanField: BooleanValuedFieldTransformer,
            serializers.CharField: StringValuedFieldTransformer,
            serializers.DateField: StringValuedFieldTransformer,
            serializers.DateTimeField: StringValuedFieldTransformer,
            serializers.DecimalField: StringValuedFieldTransformer,
            serializers.DictField: DictValuedFieldTransformer,
            serializers.FloatField: FloatValuedFieldTransformer,
            serializers.IntegerField: IntegerValuedFieldTransformer,
            serializers.ListField: ListValuedFieldTransformer,
            serializers.ManyRelatedField: ListOfStringsValuedFieldTransformer,
            serializers.ModelSerializer: RelatedValuedFieldTransformer,
            serializers.HyperlinkedRelatedField: HyperlinkedRelatedFieldTransformer,
            serializers.RelatedField: StringValuedFieldTransformer,
            serializers.TimeField: StringValuedFieldTransformer,
            serializers.UUIDField: StringValuedFieldTransformer,
        }
        transformer_class = next(
            (v for t, v in base_types.items() if isinstance(field, t)),
            GenericValuedFieldTransformer,
        )
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
    def graphene_field(self):
        return self.graphene_type(
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )


class RelatedValuedFieldTransformer(FieldTransformer):
    def __init__(self, field, type_mapping=None):
        super(RelatedValuedFieldTransformer, self).__init__(
            field, type_mapping)
        self._field_class = field.__class__
        self._is_to_many = getattr(field, 'many', False)

    def graphene_field(self):
        wrapper = graphene.List if self._is_to_many else graphene.Field
        graphene_field = wrapper(
            self.graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )
        return graphene_field

    @property
    def graphene_type(self):
        # Needs to be lazy since at this point the related
        # type may not yet have been created
        name = self._build_graphene_type_name()
        return lambda: self.type_mapping[name]

    def _build_graphene_type_name(self):
        if isinstance(self._field, ListSerializer):
            serializer_cls_name = self._field.child.__class__.__name__
        else:
            serializer_cls_name = self._field.__class__.__name__
        if serializer_cls_name == 'NestedSerializer':
            model = self._field.parent.Meta.model.__name__.lower()
            return '{}__{}_type'.format(model, self._field.field_name)
        else:
            model = self._field.Meta.model.__name__.lower()
            type_name = '{}_type'.format(model)
            types_for_model = [
                t for t in self.type_mapping if t.startswith(type_name)]
            if types_for_model:
                type_name = '{}_{}'.format(type_name, len(types_for_model) + 1)
            return type_name


class HyperlinkedRelatedFieldTransformer(RelatedValuedFieldTransformer):
    def _build_graphene_type_name(self):
        from graph_wrap.django_rest_framework.schema_factory import SchemaFactory
        views = SchemaFactory.usable_views()
        related_view_name = self._field.view_name.split('-')[0]
        related_view_set = next(
            (v for v in views if v.basename == related_view_name))
        serializer = related_view_set.get_serializer()
        model = serializer.Meta.model.__name__.lower()
        return '{}_type'.format(model)


class GenericValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = GenericScalar


class StringValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = graphene.String


class IntegerValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = graphene.Int


class FloatValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = graphene.Float


class BooleanValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = graphene.Boolean


class DecimalValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = graphene.Decimal


class Dict(graphene.Scalar):
    # replace by graphene.JSONString?
    @staticmethod
    def serialize(dt):
        if isinstance(dt, six.string_types):
            return json.loads(dt)
        return dt


class DictValuedFieldTransformer(ScalarValuedFieldTransformer):
    graphene_type = Dict


class ListValuedFieldTransformer(FieldTransformer):
    graphene_type = GenericScalar

    def graphene_field(self):
        return graphene.List(
            self.graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
            resolver=self.graphene_field_resolver_method(),
        )


class ListOfStringsValuedFieldTransformer(
        ListValuedFieldTransformer):
    graphene_type = graphene.String

