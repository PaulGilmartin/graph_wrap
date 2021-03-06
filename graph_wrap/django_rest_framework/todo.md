*. (DONE) Handle SerializerMethodField
*  (DONE) Handle custom serialization of model fields (see https://stackoverflow.com/questions/37798208/django-rest-framework-custom-serializer-method)
*. (DONE) Decide what to do about letting user add their own field types - right now we use generic (DONE: leave for v2)
*  (DONE) required fields 
*  filters ((DONE) start with supporting https://www.django-rest-framework.org/api-guide/filtering/#searchfilter, then maybe the django_filter BE?)
*. (POSTPONE) Test directives
* (POSTPONE) check write only fields

* next: django_filter
*. Ensure we can run with only one of tastypie or DRF installed.
  - next: DRF solo done. Try tastypie solo next.
* Find versions of graphene, django rest and tastypie
* Different routers? Not ModelViewSet?
* Test Hyperlinked
*. (IGNORE FOR NOW) SelectedFieldsClass will fail type checks 
* bad status codes