import json
from abc import abstractmethod
from decimal import Decimal

import graphene
import six
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from rest_framework import serializers

from graph_wrap.django_rest_framework.field_resolvers import JSONResolver


def transform_api(api):
    # api is a view set instance
    graphene_type_name = api.basename + '_type'  # Does basename limit the view type?
    serializer = api.get_serializer()
    return transform_serializer(serializer, graphene_type_name=graphene_type_name)


def transform_serializer(serializer, graphene_type_name=None):
    class_attrs = dict()

    graphene_type_name = graphene_type_name or 'from_{}_model_type'.format(
        serializer.Meta.model.__name__.lower())

    for field_name, field in serializer.fields.items():# .fields limits to views or viewsets?
        transform_field(field, field_name, class_attrs=class_attrs)
    graphene_type = type(
        str(graphene_type_name),
        (ObjectType,),
        class_attrs,
    )
    return graphene_type


def transform_field(field, field_name, class_attrs=None):
    class_attrs = dict() if class_attrs is None else class_attrs

    transformer = field_transformer(field)
    class_attrs[field_name] = transformer.graphene_field()
    resolver_method_name = 'resolve_{}'.format(field_name)
    class_attrs[resolver_method_name] = (
        transformer.graphene_field_resolver_method())


def field_transformer(field, class_attrs=None):
    """Instantiate the appropriate FieldTransformer class.

    This acts as a factory-type function, which, given
    a tastypie field as input, instantiates the appropriate
    concrete FieldTransformer class for that field.
    """
    class_attrs = dict() if class_attrs is None else class_attrs
    if hasattr(field, 'fields'):
        # Safe to assume this is a serializer?
        for field_name, field in field.fields.items():
            transform_field(field, field_name, class_attrs)

    serializer_field_to_transformer = {
        serializers.CharField: StringValuedFieldTransformer,
        serializers.IntegerField: IntegerValuedFieldTransformer,
        serializers.HyperlinkedRelatedField: RelatedValuedFieldTransformer,
    }
    try:
        transformer_class = serializer_field_to_transformer[
            field.__class__]
    except KeyError:
        raise KeyError('Field type not recognized')
    return transformer_class(field)


class FieldTransformer(object):
    _graphene_type = None

    def __init__(self, field):
        self._field = field

    @abstractmethod
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
        )


class RelatedValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'related' field."""
    def __init__(self, field):
        super(RelatedValuedFieldTransformer, self).__init__(field)
        self._field_class = field.__class__
        self._is_to_many = False  # how to determine?

    def graphene_field(self):
        wrapper = graphene.List if self._is_to_many else graphene.Field
        return wrapper(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )

    @property
    def _graphene_type(self):
        from .schema_factory import SchemaFactory
        # Needs to be lazy since at this point the related
        # type may not yet have been created
        # This isn't thread safe. We can probably pass through
        # the SchemaFactory instance to this point
        # and have api_class_to_schema as a instance attr.
        return lambda: SchemaFactory.api_class_to_schema[
            self._field.view_name]


class StringValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class IntegerValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Int


class FloatValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Float


class BooleanValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Boolean


class DateValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class DatetimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class TimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class UnicodeCompatibleDecimal(Decimal):
    """
    The `Decimal` scalar type represents a python Decimal.
    """

    @staticmethod
    def serialize(dec):
        if isinstance(dec, six.string_types):
            dec = graphene.Decimal(dec)
        assert isinstance(
            dec, graphene.Decimal), 'Received not compatible Decimal "{}"'.format(
            repr(dec)
        )
        return str(dec)


class DecimalValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = UnicodeCompatibleDecimal


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
        )


class ToOneRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    pass


class ToManyRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    _tastypie_field_is_m2m = True