from __future__ import unicode_literals

from django.db import models


class Media(models.Model):
    name = models.TextField()
    content_type = models.TextField()
    size = models.BigIntegerField()


class Author(models.Model):
    name = models.TextField()
    age = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    profile_picture = models.ForeignKey(
        Media, null=True, on_delete=models.PROTECT)


class Post(models.Model):
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(Author, null=True, on_delete=models.SET_NULL)
    files = models.ManyToManyField('Media')
    rating = models.DecimalField(null=True, decimal_places=20, max_digits=40)


