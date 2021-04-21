from __future__ import unicode_literals

import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    father_name = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    @property
    def age(self):
        age = datetime.date.today() - self.birth_date
        return age.days // 360
