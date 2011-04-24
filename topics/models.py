from django.db import models

class Topic(models.Model):
    """
    A specific topic that has images associated with it.
    """
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Image(models.Model):
    """
    A single image on a topic.
    """
    url = models.URLField();
    topic = models.ForeignKey(Topic)

    # Upper-left corner of the image
    x = models.IntegerField();
    y = models.IntegerField();

    def __unicode__(self):
        return str(self.topic) + ' | ' + str(url)

