from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class Media(models.Model):
    name = models.TextField()
    content_type = models.TextField(null=True)
    size = models.BigIntegerField(null=True)


class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    name = models.TextField()
    age = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    profile_picture = models.ForeignKey(
        Media, null=True, on_delete=models.PROTECT)

    def get_name(self):
        # Use to test custom additional serialization
        return self.name.upper()


class Post(models.Model):
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(
        Author, null=True, on_delete=models.SET_NULL, related_name='entries')
    files = models.ManyToManyField('Media')
    rating = models.DecimalField(null=True, decimal_places=20, max_digits=40)


