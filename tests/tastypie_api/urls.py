from tastypie.api import Api

from .api import AuthorResource, PostResource, MediaResource


api = Api('v1')
api.register(AuthorResource())
api.register(PostResource())
api.register(MediaResource())
