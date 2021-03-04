import graphene


def get_query_attributes(
        api,
        single_item_field_name,
        graphene_type,
        single_item_resolver_cls,
        all_items_resolver_cls,
        **filters,
):
    all_items_field_name = 'all_{}s'.format(single_item_field_name)
    single_item_resolver_name = 'resolve_{}'.format(single_item_field_name)
    all_items_resolver_name = 'resolve_{}'.format(all_items_field_name)
    return {
        single_item_field_name: graphene.Field(
            graphene_type,
            id=graphene.Int(required=True),
            name=single_item_field_name,
        ),
        all_items_field_name: graphene.List(
            graphene_type, name=all_items_field_name, **filters),
        single_item_resolver_name: single_item_resolver_cls(
            field_name=single_item_field_name, api=api),
        all_items_resolver_name: all_items_resolver_cls(
            field_name=all_items_field_name, api=api),
    }
