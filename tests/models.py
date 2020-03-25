from django.db import models


class Author(models.Model):
    name = models.TextField()
    age = models.TextField()


class Post(models.Model):
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(Author, null=True, on_delete=models.SET_NULL)
    files = models.ManyToManyField('Media')


class Media(models.Model):
    name = models.TextField()
    content_type = models.TextField()
    size = models.BigIntegerField()



