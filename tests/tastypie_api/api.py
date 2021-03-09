from __future__ import unicode_literals

from tastypie import fields
from tastypie.resources import ModelResource
from tests.models import Author, Post, Media


class AuthorResource(ModelResource):
    posts = fields.ManyToManyField(
        'tests.tastypie_api.api.PostResource', attribute='entries')

    class Meta:
        queryset = Author.objects.all()
        resource_name = u'author'
        filtering = {
            'age': ('exact',),
            'name': ('exact',),
        }


class PostResource(ModelResource):
    author = fields.ForeignKey(AuthorResource, attribute='author', null=True)
    files = fields.ManyToManyField('tests.tastypie_api.api.MediaResource', attribute='files')
    date = fields.DateTimeField('date')
    rating = fields.DecimalField('rating', null=True)
    content = fields.CharField('content')

    class Meta:
        queryset = Post.objects.all()
        resource_name = u'post'


class MediaResource(ModelResource):
    class Meta:
        queryset = Media.objects.all()
        resource_name = u'media'

