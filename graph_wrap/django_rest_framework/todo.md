*. (DONE) Handle SerializerMethodField
*  (DONE) Handle custom serialization of model fields (see https://stackoverflow.com/questions/37798208/django-rest-framework-custom-serializer-method)
*. (DONE) Decide what to do about letting user add their own field types - right now we use generic (DONE: leave for v2)
*  (DONE) required fields 
*  filters (start with supporting https://www.django-rest-framework.org/api-guide/filtering/#searchfilter, then maybe the django_filter BE?)
   - next: GraphQLResolveInfoTransformer - the __init__ needs to set query_params on the request using the field_kwargs
   - probably need to subclass for DRF

*. Test directives
* check write only fields
* Different routers? Not ModelViewSet?
* Test Hyperlinked
*. Ensure we can run with only one of tastypie or DRF installed
*. (IGNORE FOR NOW) SelectedFieldsClass will fail type checks 
* bad status codes