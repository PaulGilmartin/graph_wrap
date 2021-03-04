*. (IGNORE FOR NOW) SelectedFieldsClass will fail type checks 
*. (DONE) Handle SerializerMethodField
*  (DONE) Handle custom serialization of model fields (se https://stackoverflow.com/questions/37798208/django-rest-framework-custom-serializer-method)
*. (DONE) Decide what to do about letting user add their own field types - right now we use generic (DONE: leave for v2)
*  required fields 
* filters
*. Ensure we can run with only one of tastypie or DRF installed
*. Factor out shared logic (api_transformer.py next. Also query attribtues)
* Serializers which don't inherit from ModelSerializer
* check write only fields
* Different routers? Not ModelViewSet?
*. Test directives
