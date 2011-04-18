from django.db import models

class Topic(models.Model):
    """
    A specific topic that has images associated with it.
    """
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
