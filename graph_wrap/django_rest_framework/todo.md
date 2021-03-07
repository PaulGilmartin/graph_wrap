*. (DONE) Handle SerializerMethodField
*  (DONE) Handle custom serialization of model fields (see https://stackoverflow.com/questions/37798208/django-rest-framework-custom-serializer-method)
*. (DONE) Decide what to do about letting user add their own field types - right now we use generic (DONE: leave for v2)
*  (DONE) required fields 
* Versioning:
  - (DONE) Can run with only tastypie or only DRF
  - (DONE) Test different versions. Summary: everything should work if we
    state that a prequisite is Django>=2.2 and djangorestframework >= 3.0.0 OR
    tastypie >= 0.14.3 and have graphene-django==2.15.0
* (DONE for now) bad status codes 
* (DONE) Test authorization
*. (IGNORE FOR NOW) SelectedFieldsClass will fail type checks 
*. (POSTPONE) Test directives
* (POSTPONE) check write only fields
* (DONE) Not ModelViewSet?
* Different routers? 

* Test Hyperlinked
* django_filter
* test on intempus api
